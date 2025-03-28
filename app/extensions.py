from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)

# Application configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///powerbank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this in production

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    balance = db.Column(db.Float, default=0.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)

class PowerBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # Options: available, rented, maintenance

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    powerbank_id = db.Column(db.Integer, db.ForeignKey('power_bank.id'), nullable=False)
    rental_time = db.Column(db.DateTime, default=datetime.utcnow)
    return_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # Options: active, completed

# Endpoints

## User Registration
@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    phone_number = data.get('phone_number')

    if not username or not password or not email:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    user = User(username=username, email=email, phone_number=phone_number)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

## User Login
@app.route('/login', methods=['POST'])
def login():
    """
    Log in a user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

## Get User Profile
@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    """
    Retrieve the profile of the logged-in user.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'balance': user.balance
        }), 200
    else:
        return jsonify({'message': 'User not found'}), 404

## Update User Profile
@app.route('/user', methods=['PUT'])
@jwt_required()
def update_user():
    """
    Update the profile of the logged-in user.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    if 'email' in data:
        user.email = data['email']
    if 'phone_number' in data:
        user.phone_number = data['phone_number']

    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200

## List All Locations
@app.route('/locations', methods=['GET'])
def get_locations():
    """
    List all locations.
    """
    locations = Location.query.all()
    return jsonify([{
        'id': loc.id,
        'name': loc.name,
        'address': loc.address
    } for loc in locations]), 200

## List Available Power Banks at a Location
@app.route('/locations/<int:location_id>/powerbanks', methods=['GET'])
def get_available_powerbanks(location_id):
    """
    List all available power banks at a specific location.
    """
    powerbanks = PowerBank.query.filter_by(location_id=location_id, status='available').all()
    return jsonify([{
        'id': pb.id,
        'location_id': pb.location_id,
        'status': pb.status
    } for pb in powerbanks]), 200

## Rent a Power Bank
@app.route('/rent', methods=['POST'])
@jwt_required()
def rent_powerbank():
    """
    Rent a power bank.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    powerbank_id = data.get('powerbank_id')

    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank or powerbank.status != 'available':
        return jsonify({'message': 'Power bank not available'}), 400

    rental_cost = 10.0  # Fixed cost for simplicity
    user = User.query.get(user_id)
    if user.balance < rental_cost:
        return jsonify({'message': 'Insufficient balance'}), 400

    user.balance -= rental_cost
    powerbank.status = 'rented'
    rental = Rental(user_id=user_id, powerbank_id=powerbank_id)
    db.session.add(rental)
    db.session.commit()

    return jsonify({'message': 'Power bank rented successfully', 'rental_id': rental.id}), 201

## Return a Power Bank
@app.route('/return', methods=['POST'])
@jwt_required()
def return_powerbank():
    """
    Return a rented power bank.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    rental_id = data.get('rental_id')

    rental = Rental.query.get(rental_id)
    if not rental or rental.user_id != user_id or rental.status != 'active':
        return jsonify({'message': 'Invalid rental'}), 400

    rental.return_time = datetime.utcnow()
    rental.status = 'completed'
    powerbank = PowerBank.query.get(rental.powerbank_id)
    powerbank.status = 'available'
    db.session.commit()

    return jsonify({'message': 'Power bank returned successfully'}), 200

## Get User's Active Rentals
@app.route('/rentals', methods=['GET'])
@jwt_required()
def get_active_rentals():
    """
    Retrieve the active rentals of the logged-in user.
    """
    user_id = get_jwt_identity()
    rentals = Rental.query.filter_by(user_id=user_id, status='active').all()
    return jsonify([{
        'id': rental.id,
        'powerbank_id': rental.powerbank_id,
        'rental_time': rental.rental_time.isoformat()
    } for rental in rentals]), 200

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
