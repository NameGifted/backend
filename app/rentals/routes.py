from flask import Blueprint, request, jsonify
from models import Rental, User, PowerBank
from db import db
from datetime import datetime

# Define the Blueprint for rentals-related routes
rentals_bp = Blueprint('rentals', __name__)

# Endpoint to create a new rental (rent a power bank)
@rentals_bp.route('/rentals', methods=['POST'])
def create_rental():
    """
    Create a new rental for a user to rent a power bank.
    Expects JSON body with 'user_id' and 'powerbank_id'.
    Returns the created rental details on success.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    powerbank_id = data.get('powerbank_id')
    
    # Validate user_id and powerbank_id
    try:
        user_id = int(user_id)
        powerbank_id = int(powerbank_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid user_id or powerbank_id'}), 400
    
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if the power bank exists and is available
    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank:
        return jsonify({'error': 'PowerBank not found'}), 404
    if not powerbank.is_available:
        return jsonify({'error': 'PowerBank is not available'}), 400
    
    # Create a new rental record
    rental = Rental(
        user_id=user_id,
        powerbank_id=powerbank_id,
        start_time=datetime.utcnow(),
        status='active'
    )
    db.session.add(rental)
    
    # Mark the power bank as unavailable
    powerbank.is_available = False
    db.session.commit()
    
    # Return the created rental details
    return jsonify(rental.to_dict()), 201

# Endpoint to return a rented power bank
@rentals_bp.route('/rentals/<int:rental_id>', methods=['PATCH'])
def return_rental(rental_id):
    """
    Update a rental to mark it as returned.
    Sets the end_time and changes status to 'completed'.
    Returns the updated rental details on success.
    """
    # Fetch the rental by ID
    rental = Rental.query.get(rental_id)
    if not rental:
        return jsonify({'error': 'Rental not found'}), 404
    
    # Check if the rental is active
    if rental.status != 'active':
        return jsonify({'error': 'Rental is not active'}), 400
    
    # Update rental details to mark it as returned
    rental.end_time = datetime.utcnow()
    rental.status = 'completed'
    
    # Mark the power bank as available again
    powerbank = PowerBank.query.get(rental.powerbank_id)
    if powerbank:
        powerbank.is_available = True
    
    db.session.commit()
    
    # Return the updated rental details
    return jsonify(rental.to_dict()), 200

# Endpoint to get details of a specific rental
@rentals_bp.route('/rentals/<int:rental_id>', methods=['GET'])
def get_rental(rental_id):
    """
    Retrieve details of a specific rental by its ID.
    Returns the rental details if found.
    """
    # Fetch the rental by ID
    rental = Rental.query.get(rental_id)
    if not rental:
        return jsonify({'error': 'Rental not found'}), 404
    
    # Return the rental details
    return jsonify(rental.to_dict()), 200

# Endpoint to get a list of rentals with optional filters
@rentals_bp.route('/rentals', methods=['GET'])
def get_rentals():
    """
    Retrieve a list of rentals, optionally filtered by user_id and/or status.
    Query parameters: 'user_id' (int), 'status' (e.g., 'active', 'completed').
    Returns a list of rental details.
    """
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    # Start with the base query
    query = Rental.query
    
    # Apply user_id filter if provided
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user_id'}), 400
        query = query.filter_by(user_id=user_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter_by(status=status)
    
    # Execute the query and fetch all matching rentals
    rentals = query.all()
    
    # Return the list of rentals
    return jsonify([rental.to_dict() for rental in rentals]), 200
