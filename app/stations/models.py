from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Initialize the FastAPI application
app = FastAPI()

# --- Pydantic Models ---

## Input model for creating a station
class StationIn(BaseModel):
    location: str

## Base model for a station
class Station(BaseModel):
    id: int
    location: str

## Output model for a station, including the count of available power banks
class StationOut(BaseModel):
    id: int
    location: str
    available_powerbanks: int

## Input model for creating or updating a power bank
class PowerBankIn(BaseModel):
    status: str

## Base model for a power bank
class PowerBank(BaseModel):
    id: int
    station_id: int
    status: str

# --- In-memory data stores (simulating a database) ---

stations = [
    {"id": 1, "location": "Station A"},
    {"id": 2, "location": "Station B"},
]

powerbanks = [
    {"id": 1, "station_id": 1, "status": "available"},
    {"id": 2, "station_id": 1, "status": "rented"},
    {"id": 3, "station_id": 2, "status": "available"},
]

# --- Station Endpoints ---

@app.get("/stations", response_model=List[StationOut])
def list_stations():
    """
    List all stations with the number of available power banks.
    
    Returns:
        A list of stations with the count of available power banks.
    """
    def get_available_powerbanks(station_id):
        return len([pb for pb in powerbanks if pb["station_id"] == station_id and pb["status"] == "available"])

    return [
        {"id": s["id"], "location": s["location"], "available_powerbanks": get_available_powerbanks(s["id"])}
        for s in stations
    ]

@app.get("/stations/{station_id}", response_model=StationOut)
def get_station(station_id: int):
    """
    Get details of a specific station with the number of available power banks.
    
    Args:
        station_id: The ID of the station to retrieve.
    
    Returns:
        The station details including the count of available power banks.
    
    Raises:
        HTTPException: 404 if the station is not found.
    """
    station = next((s for s in stations if s["id"] == station_id), None)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    available_powerbanks = len([pb for pb in powerbanks if pb["station_id"] == station_id and pb["status"] == "available"])
    return {"id": station["id"], "location": station["location"], "available_powerbanks": available_powerbanks}

@app.post("/stations", response_model=Station)
def create_station(station_in: StationIn):
    """
    Create a new station.
    
    Args:
        station_in: The station data to create.
    
    Returns:
        The created station object.
    """
    new_id = len(stations) + 1
    new_station = {"id": new_id, "location": station_in.location}
    stations.append(new_station)
    return new_station

@app.put("/stations/{station_id}", response_model=Station)
def update_station(station_id: int, station_in: StationIn):
    """
    Update a station's location.
    
    Args:
        station_id: The ID of the station to update.
        station_in: The updated station data.
    
    Returns:
        The updated station object.
    
    Raises:
        HTTPException: 404 if the station is not found.
    """
    station = next((s for s in stations if s["id"] == station_id), None)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    station["location"] = station_in.location
    return station
