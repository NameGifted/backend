from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Initialize the FastAPI application
app = FastAPI(title="Power Bank Rental Service")

# --- Data Models ---
# User Models
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

# Station Models
class StationBase(BaseModel):
    location: str  # Simplified as a string; could be latitude/longitude in a real app
    address: str
    powerbanks_available: int

class Station(StationBase):
    id: int

# PowerBank Models
class PowerBankBase(BaseModel):
    station_id: int
    status: str  # e.g., "available", "rented", "maintenance"

class PowerBank(PowerBankBase):
    id: int

# Rental Models
class RentalBase(BaseModel):
    user_id: int
    powerbank_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # e.g., "active", "completed"

class RentalCreate(BaseModel):
    powerbank_id: int

class Rental(RentalBase):
    id: int

# --- Dummy Databases ---
# These simulate a database for demonstration purposes
users_db = [{"id": 1, "name": "Alice", "email": "alice@example.com"}]
stations_db = [{"id": 1, "location": "Station A", "address": "123 Main St", "powerbanks_available": 5}]
powerbanks_db = [
    {"id": 1, "station_id": 1, "status": "available"},
    {"id": 2, "station_id": 1, "status": "available"}
]
rentals_db = []

# --- Dependency ---
# Dummy function to simulate getting the current authenticated user
def get_current_user():
    if users_db:
        return users_db[0]  # Returns the first user as the "current" user
    else:
        raise HTTPException(status_code=404, detail="No users found")

# --- Endpoints ---

## User Endpoints
@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    """Register a new user."""
    new_user = {"id": len(users_db) + 1, "name": user.name, "email": user.email}
    users_db.append(new_user)
    return new_user

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int):
    """Get details of a specific user by ID."""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

## Station Endpoints
@app.get("/stations", response_model=List[Station])
def read_stations():
    """List all stations."""
    return stations_db

@app.get("/stations/{station_id}", response_model=Station)
def read_station(station_id: int):
    """Get details of a specific station by ID."""
    for station in stations_db:
        if station["id"] == station_id:
            return station
    raise HTTPException(status_code=404, detail="Station not found")

## PowerBank Endpoints
@app.get("/powerbanks", response_model=List[PowerBank])
def read_powerbanks():
    """List all power banks."""
    return powerbanks_db

@app.get("/powerbanks/{powerbank_id}", response_model=PowerBank)
def read_powerbank(powerbank_id: int):
    """Get details of a specific power bank by ID."""
    for pb in powerbanks_db:
        if pb["id"] == powerbank_id:
            return pb
    raise HTTPException(status_code=404, detail="PowerBank not found")

## Rental Endpoints
@app.post("/rentals", response_model=Rental)
def create_rental(rental: RentalCreate, current_user: dict = Depends(get_current_user)):
    """Rent a power bank."""
    # Check if the power bank is available
    powerbank = None
    for pb in powerbanks_db:
        if pb["id"] == rental.powerbank_id and pb["status"] == "available":
            powerbank = pb
            break
    if not powerbank:
        raise HTTPException(status_code=400, detail="PowerBank not available")

    # Create a new rental record
    new_rental = {
        "id": len(rentals_db) + 1,
        "user_id": current_user["id"],
        "powerbank_id": rental.powerbank_id,
        "start_time": datetime.now(),
        "end_time": None,
        "status": "active"
    }
    rentals_db.append(new_rental)
    powerbank["status"] = "rented"  # Update power bank status
    return new_rental

@app.put("/rentals/{rental_id}/return", response_model=Rental)
def return_powerbank(rental_id: int, current_user: dict = Depends(get_current_user)):
    """Return a rented power bank."""
    for rental in rentals_db:
        if rental["id"] == rental_id and rental["user_id"] == current_user["id"] and rental["status"] == "active":
            rental["end_time"] = datetime.now()
            rental["status"] = "completed"
            # Update power bank status
            for pb in powerbanks_db:
                if pb["id"] == rental["powerbank_id"]:
                    pb["status"] = "available"
                    break
            return rental
    raise HTTPException(status_code=400, detail="Rental not found or not active")

@app.get("/rentals", response_model=List[Rental])
def read_rentals(current_user: dict = Depends(get_current_user)):
    """List all rentals for the current user."""
    return [rental for rental in rentals_db if rental["user_id"] == current_user["id"]]
