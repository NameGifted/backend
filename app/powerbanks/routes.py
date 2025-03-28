from flask import Blueprint, request, jsonify
from models import PowerBank
from db import db

# Define the Blueprint for powerbanks-related routes
powerbanks_bp = Blueprint('powerbanks', __name__)

# Endpoint to create a new power bank
@powerbanks_bp.route('/powerbanks', methods=['POST'])
def create_powerbank():
    """
    Create a new power bank entry.
    Expects JSON body with 'serial_number', 'capacity', and 'location'.
    Returns the created power bank details on success.
    """
    data = request.get_json()
    serial_number = data.get('serial_number')
    capacity = data.get('capacity')
    location = data.get('location')
    
    # Validate that all required fields are provided
    if not serial_number or not capacity or not location:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if a power bank with the same serial number already exists
    existing_powerbank = PowerBank.query.filter_by(serial_number=serial_number).first()
    if existing_powerbank:
        return jsonify({'error': 'PowerBank with this serial number already exists'}), 400
    
    # Create a new power bank record
    powerbank = PowerBank(
        serial_number=serial_number,
        capacity=capacity,
        location=location,
        is_available=True  # New power banks are available by default
    )
    db.session.add(powerbank)
    db.session.commit()
    
    # Return the created power bank details
    return jsonify(powerbank.to_dict()), 201

# Endpoint to update an existing power bank
@powerbanks_bp.route('/powerbanks/<int:powerbank_id>', methods=['PATCH'])
def update_powerbank(powerbank_id):
    """
    Update an existing power bank's details.
    Expects JSON body with optional fields: 'capacity', 'location', 'is_available'.
    Returns the updated power bank details on success.
    """
    # Fetch the power bank by ID
    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank:
        return jsonify({'error': 'PowerBank not found'}), 404
    
    data = request.get_json()
    
    # Update fields if provided in the request
    if 'capacity' in data:
        powerbank.capacity = data['capacity']
    if 'location' in data:
        powerbank.location = data['location']
    if 'is_available' in data:
        powerbank.is_available = data['is_available']
    
    db.session.commit()
    
    # Return the updated power bank details
    return jsonify(powerbank.to_dict()), 200

# Endpoint to get a list of power banks with optional filters
@powerbanks_bp.route('/powerbanks', methods=['GET'])
def get_powerbanks():
    """
    Retrieve a list of power banks, optionally filtered by location and/or availability.
    Query parameters: 'location' (string), 'is_available' (boolean).
    Returns a list of power bank details.
    """
    location = request.args.get('location')
    is_available = request.args.get('is_available')
    
    # Start with the base query
    query = PowerBank.query
    
    # Apply location filter if provided
    if location:
        query = query.filter_by(location=location)
    
    # Apply availability filter if provided
    if is_available is not None:
        # Convert string to boolean
        if is_available.lower() in ['true', '1']:
            is_available = True
        elif is_available.lower() in ['false', '0']:
            is_available = False
        else:
            return jsonify({'error': 'Invalid value for is_available'}), 400
        query = query.filter_by(is_available=is_available)
    
    # Execute the query and fetch all matching power banks
    powerbanks = query.all()
    
    # Return the list of power banks
    return jsonify([powerbank.to_dict() for powerbank in powerbanks]), 200

# Endpoint to get details of a specific power bank
@powerbanks_bp.route('/powerbanks/<int:powerbank_id>', methods=['GET'])
def get_powerbank(powerbank_id):
    """
    Retrieve details of a specific power bank by its ID.
    Returns the power bank details if found.
    """
    # Fetch the power bank by ID
    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank:
        return jsonify({'error': 'PowerBank not found'}), 404
    
    # Return the power bank details
    return jsonify(powerbank.to_dict()), 200
