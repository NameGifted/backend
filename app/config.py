from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import datetime

# Initialize FastAPI application
app = FastAPI(title="Power Bank Rental Service")

# --- Data Models ---

class UserIn(BaseModel):
    """Input model for creating a new user."""
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    """Output model for user data (excluding password)."""
    id: int
    name: str
    email: str

class Station(BaseModel):
    """Model for a rental station."""
    id: int
    location: str
    powerbanks_available: int

class PowerBank(BaseModel):
    """Model for a power bank."""
    id: int
    station_id: int
    status: str  # e.g., "available", "rented"

class RentalIn(BaseModel):
    """Input model for renting a power bank."""
    powerbank_id: int

class RentalOut(BaseModel):
    """Output model for rental data."""
    id: int
    user_id: int
    powerbank_id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    status: str  # e.g., "active", "completed"

class StationIn(BaseModel):
    """Input model for creating a new station."""
    location: str
    powerbanks_available: int = 0

class PowerBankIn(BaseModel):
    """Input model for creating a new power bank."""
    station_id: int
    status: str = "available"

# --- Dummy Databases ---
# Note: Replace with a real database in a production environment
users = [{"id": 1, "name": "Admin", "email": "admin@example.com"}]
stations = [
    {"id": 1, "location": "Station A", "powerbanks_available": 2},
    {"id": 2, "location": "Station B", "powerbanks_available": 1},
]
powerbanks = [
    {"id": 1, "station_id": 1, "status": "available"},
    {"id": 2, "station_id": 1, "status": "available"},
    {"id": 3, "station_id": 2, "status": "rented"},
]
rentals = []

# --- Dependencies ---

def get_current_user():
    """Dummy dependency to simulate retrieving the current user."""
    if users:
        return users[0]  # Always return the first user for this example
    else:
        raise HTTPException(status_code=404, detail="No users found")

def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to restrict access to admin users (id=1)."""
    if current_user["id"] != 1:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# --- Endpoints ---

# User Management
@app.post("/users", response_model=UserOut)
def create_user(user: UserIn):
    """Register a new user."""
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "email": user.email,
        # Note: In a real app, password should be hashed
    }
    users.append(new_user)
    return new_user

# Station Management
@app.get("/stations", response_model=List[Station])
def get_stations():
    """Retrieve a list of all stations."""
    return stations

@app.get("/stations/{station_id}", response_model=Station)
def get_station(station_id: int):
    """Retrieve details of a specific station by ID."""
    station = next((s for s in stations if s["id"] == station_id), None)
    if station:
        return station
    raise HTTPException(status_code=404, detail="Station not found")

@app.post("/stations", response_model=Station)
def create_station(station: StationIn, admin: dict = Depends(get_current_admin)):
    """Create a new station (admin only)."""
    new_station = {"id": len(stations) + 1, **station.dict()}
    stations.append(new_station)
    return new_station

# Power Bank Management
@app.get("/stations/{station_id}/powerbanks", response_model=List[PowerBank])
def get_powerbanks(station_id: int):
    """Retrieve a list of power banks at a specific station."""
    station_powerbanks = [pb for pb in powerbanks if pb["station_id"] == station_id]
    return station_powerbanks

@app.post("/powerbanks", response_model=PowerBank)
def create_powerbank(powerbank: PowerBankIn, admin: dict = Depends(get_current_admin)):
    """Create a new power bank (admin only)."""
    new_powerbank = {"id": len(powerbanks) + 1, **powerbank.dict()}
    powerbanks.append(new_powerbank)
    if new_powerbank["status"] == "available":
        station = next((s for s in stations if s["id"] == new_powerbank["station_id"]), None)
        if station:
            station["powerbanks_available"] += 1
    return new_powerbank

# Rental Management
@app.post("/rentals", response_model=RentalOut)
def rent_powerbank(rental: RentalIn, current_user: dict = Depends(get_current_user)):
    """Rent a power bank."""
    powerbank_id = rental.powerbank_id
    powerbank = next((pb for pb in powerbanks if pb["id"] == powerbank_id), None)
    if not powerbank:
        raise HTTPException(status_code=404, detail="Powerbank not found")
    if powerbank["status"] != "available":
        raise HTTPException(status_code=400, detail="Powerbank not available")

    new_rental = {
        "id": len(rentals) + 1,
        "user_id": current_user["id"],
        "powerbank_id": powerbank_id,
        "start_time": datetime.datetime.now(),
        "end_time": None,
        "status": "active"
    }
    rentals.append(new_rental)
    powerbank["status"] = "rented"
    station = next((s for s in stations if s["id"] == powerbank["station_id"]), None)
    if station:
        station["powerbanks_available"] -= 1
    return new_rental

@app.put("/rentals/{rental_id}/return", response_model=RentalOut)
def return_powerbank(rental_id: int, current_user: dict = Depends(get_current_user)):
    """Return a rented power bank."""
    rental = next((r for r in rentals if r["id"] == rental_id and r["user_id"] == current_user["id"]), None)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if rental["status"] != "active":
        raise HTTPException(status_code=400, detail="Rental is not active")

    rental["end_time"] = datetime.datetime.now()
    rental["status"] = "completed"
    powerbank = next(pb for pb in powerbanks if pb["id"] == rental["powerbank_id"])
    powerbank["status"] = "available"
    station = next((s for s in stations if s["id"] == powerbank["station_id"]), None)
    if station:
        station["powerbanks_available"] += 1
    return rental

@app.get("/rentals", response_model=List[RentalOut])
def get_rentals(current_user: dict = Depends(get_current_user)):
    """Retrieve rental history for the current user."""
    user_rentals = [r for r in rentals if r["user_id"] == current_user["id"]]
    return user_rentals

@app.get("/rentals/active", response_model=List[RentalOut])
def get_active_rentals(current_user: dict = Depends(get_current_user)):
    """Retrieve active rentals for the current user."""
    active_rentals = [r for r in rentals if r["user_id"] == current_user["id"] and r["status"] == "active"]
    return active_rentals
