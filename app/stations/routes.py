from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import schemas, models
from ..database import get_db
from ..auth import get_current_user

# Initialize the API router for station-related endpoints
router = APIRouter(
    prefix="/stations",
    tags=["stations"]
)

# Endpoint to create a new station (Admin only)
@router.post("/", response_model=schemas.Station)
def create_station(
    station: schemas.StationCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Create a new station in the system. Only accessible to admin users.
    
    Args:
        station: The station data to create (name, location, capacity, available_power_banks).
        db: Database session dependency.
        current_user: The authenticated user making the request.
    
    Returns:
        The created station object.
    
    Raises:
        HTTPException: 403 if the user is not an admin, 400 if available_power_banks exceeds capacity.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    if station.available_power_banks > station.capacity:
        raise HTTPException(status_code=400, detail="Available power banks cannot exceed capacity")
    
    db_station = models.StationDB(**station.dict())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

# Endpoint to retrieve a list of all stations
@router.get("/", response_model=List[schemas.Station])
def read_stations(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Retrieve a paginated list of all stations.
    
    Args:
        skip: Number of records to skip (for pagination).
        limit: Maximum number of records to return (for pagination).
        db: Database session dependency.
    
    Returns:
        A list of station objects.
    """
    stations = db.query(models.StationDB).offset(skip).limit(limit).all()
    return stations

# Endpoint to retrieve details of a specific station
@router.get("/{station_id}", response_model=schemas.Station)
def read_station(
    station_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve details of a specific station by its ID.
    
    Args:
        station_id: The ID of the station to retrieve.
        db: Database session dependency.
    
    Returns:
        The station object.
    
    Raises:
        HTTPException: 404 if the station is not found.
    """
    station = db.query(models.StationDB).filter(models.StationDB.id == station_id).first()
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station

# Endpoint to update an existing station (Admin only)
@router.put("/{station_id}", response_model=schemas.Station)
def update_station(
    station_id: int,
    station_update: schemas.StationUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Update an existing station's information. Only accessible to admin users.
    
    Args:
        station_id: The ID of the station to update.
        station_update: The updated station data (fields are optional).
        db: Database session dependency.
        current_user: The authenticated user making the request.
    
    Returns:
        The updated station object.
    
    Raises:
        HTTPException: 403 if the user is not an admin, 404 if the station is not found,
                       400 if available_power_banks exceeds capacity or capacity is less than current available_power_banks.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_station = db.query(models.StationDB).filter(models.StationDB.id == station_id).first()
    if db_station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    update_data = station_update.dict(exclude_unset=True)
    if "available_power_banks" in update_data and "capacity" in update_data:
        if update_data["available_power_banks"] > update_data["capacity"]:
            raise HTTPException(status_code=400, detail="Available power banks cannot exceed capacity")
    elif "available_power_banks" in update_data:
        if update_data["available_power_banks"] > db_station.capacity:
            raise HTTPException(status_code=400, detail="Available power banks cannot exceed capacity")
    elif "capacity" in update_data:
        if db_station.available_power_banks > update_data["capacity"]:
            raise HTTPException(status_code=400, detail="Capacity cannot be less than available power banks")
    
    for key, value in update_data.items():
        setattr(db_station, key, value)
    db.commit()
    db.refresh(db_station)
    return db_station

# Endpoint to delete a station (Admin only)
@router.delete("/{station_id}")
def delete_station(
    station_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Delete a station from the system. Only accessible to admin users.
    
    Args:
        station_id: The ID of the station to delete.
        db: Database session dependency.
        current_user: The authenticated user making the request.
    
    Returns:
        A confirmation message.
    
    Raises:
        HTTPException: 403 if the user is not an admin, 404 if the station is not found.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_station = db.query(models.StationDB).filter(models.StationDB.id == station_id).first()
    if db_station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    
    db.delete(db_station)
    db.commit()
    return {"message": "Station deleted"}
