from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Initialize the FastAPI app
app = FastAPI()

# --- Pydantic Models ---

## Base model for a rental
class Rental(BaseModel):
    id: int
    user_id: int
    powerbank_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # e.g., "active", "completed"

## Input model for creating a rental
class RentalIn(BaseModel):
    user_id: int
    powerbank_id: int

## Output model for a rental
class RentalOut(BaseModel):
    id: int
    user_id: int
    powerbank_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str

## Base model for a power bank
class PowerBank(BaseModel):
    id: int
    status: str  # e.g., "available", "rented"

# --- In-memory data stores (simulating a database) ---

rentals = []
powerbanks = [
    {"id": 1, "status": "available"},
    {"id": 2, "status": "available"},
    {"id": 3, "status": "rented"},
]

# --- Rental Endpoints ---

@app.get("/rentals", response_model=List[RentalOut])
def list_rentals():
    """
    List all rentals.
    
    Returns:
        A list of rental objects.
    """
    return rentals

@app.get("/rentals/{rental_id}", response_model=RentalOut)
def get_rental(rental_id: int):
    """
    Get details of a specific rental.
    
    Args:
        rental_id: The ID of the rental to retrieve.
    
    Returns:
        The rental object if found.
    
    Raises:
        HTTPException: 404 if the rental is not found.
    """
    rental = next((r for r in rentals if r["id"] == rental_id), None)
    if rental is None:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental

@app.post("/rentals", response_model=RentalOut)
def create_rental(rental_in: RentalIn):
    """
    Create a new rental.
    
    Args:
        rental_in: The rental data to create.
    
    Returns:
        The created rental object.
    
    Raises:
        HTTPException: 404 if the power bank is not found, 400 if the power bank is not available.
    """
    # Check if the power bank exists and is available
    powerbank = next((pb for pb in powerbanks if pb["id"] == rental_in.powerbank_id), None)
    if powerbank is None:
        raise HTTPException(status_code=404, detail="PowerBank not found")
    if powerbank["status"] != "available":
        raise HTTPException(status_code=400, detail="PowerBank not available")
    
    # Create a new rental record
    new_id = len(rentals) + 1
    new_rental = {
        "id": new_id,
        "user_id": rental_in.user_id,
        "powerbank_id": rental_in.powerbank_id,
        "start_time": datetime.now(),
        "end_time": None,
        "status": "active"
    }
    rentals.append(new_rental)
    powerbank["status"] = "rented"  # Update power bank status
    return new_rental

@app.put("/rentals/{rental_id}/return", response_model=RentalOut)
def return_powerbank(rental_id: int):
    """
    Return a power bank and complete the rental.
    
    Args:
        rental_id: The ID of the rental to return.
    
    Returns:
        The updated rental object.
    
    Raises:
        HTTPException: 404 if the rental is not found or not active.
    """
    # Find an active rental by ID
    rental = next((r for r in rentals if r["id"] == rental_id and r["status"] == "active"), None)
    if rental is None:
        raise HTTPException(status_code=404, detail="Active rental not found")
    
    # Update rental details
    rental["end_time"] = datetime.now()
    rental["status"] = "completed"
    
    # Update power bank status to available
    powerbank = next((pb for pb in powerbanks if pb["id"] == rental["powerbank_id"]), None)
    if powerbank:
        powerbank["status"] = "available"
    
    return rental

# Optional: Run the app directly (for testing purposes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
