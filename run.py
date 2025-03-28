from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///powerbank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key in production
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class PowerBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, rented, maintenance
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    power_bank_id = db.Column(db.Integer, db.ForeignKey('power_bank.id'), nullable=False)
    rent_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    return_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed

# Create database tables
with app.app_context():
    db.create_all()

# Admin required decorator
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

# User Endpoints
@app.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'Username or email already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """Log in a user and return a JWT token."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Get the profile of the logged-in user."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    }), 200

# Station Endpoints
@app.route('/stations', methods=['GET'])
def get_stations():
    """List all stations."""
    stations = Station.query.all()
    return jsonify([{
        'id': station.id,
        'name': station.name,
        'location': station.location
    } for station in stations]), 200

@app.route('/stations/<int:station_id>', methods=['GET'])
def get_station(station_id):
    """Get details of a specific station."""
    station = Station.query.get(station_id)
    if not station:
        return jsonify({'message': 'Station not found'}), 404
    
    power_banks = PowerBank.query.filter_by(station_id=station_id, status='available').all()
    return jsonify({
        'id': station.id,
        'name': station.name,
        'location': station.location,
        'available_power_banks': len(power_banks)
    }), 200

# Power Bank Endpoints
@app.route('/powerbanks/<int:powerbank_id>', methods=['GET'])
def get_powerbank(powerbank_id):
    """Get details of a specific power bank."""
    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank:
        return jsonify({'message': 'Power bank not found'}), 404
    
    return jsonify({
        'id': powerbank.id,
        'station_id': powerbank.station_id,
        'status': powerbank.status
    }), 200

# Rental Endpoints
@app.route('/rent', methods=['POST'])
@jwt_required()
def rent_powerbank():
    """Rent a power bank."""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    powerbank_id = data.get('powerbank_id')
    
    powerbank = PowerBank.query.get(powerbank_id)
    if not powerbank or powerbank.status != 'available':
        return jsonify({'message': 'Power bank not available'}), 400
    
    active_rental = Rental.query.filter_by(user_id=current_user_id, status='active').first()
    if active_rental:
        return jsonify({'message': 'You already have an active rental'}), 400
    
    new_rental = Rental(user_id=current_user_id, power_bank_id=powerbank_id)
    powerbank.status = 'rented'
    db.session.add(new_rental)
    db.session.commit()
    
    return jsonify({'message': 'Power bank rented successfully', 'rental_id': new_rental.id}), 201

@app.route('/return', methods=['POST'])
@jwt_required()
def return_powerbank():
    """Return a rented power bank."""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    rental_id = data.get('rental_id')
    station_id = data.get('station_id')
    
    rental = Rental.query.get(rental_id)
    if not rental or rental.user_id != current_user_id or rental.status != 'active':
        return jsonify({'message': 'Invalid rental'}), 400
    
    powerbank = PowerBank.query.get(rental.power_bank_id)
    powerbank.status = 'available'
    powerbank.station_id = station_id
    rental.return_time = datetime.datetime.utcnow()
    rental.status = 'completed'
    
    rental_duration = (rental.return_time - rental.rent_time).total_seconds() / 3600
    amount = rental_duration * 1  # $1 per hour
    new_payment = Payment(rental_id=rental_id, amount=amount, status='pending')
    db.session.add(new_payment)
    db.session.commit()
    
    return jsonify({'message': 'Power bank returned successfully', 'payment_id': new_payment.id}), 200

@app.route('/rentals', methods=['GET'])
@jwt_required()
def get_rentals():
    """Get rental history of the logged-in user."""
    current_user_id = get_jwt_identity()
    rentals = Rental.query.filter_by(user_id=current_user_id).all()
    return jsonify([{
        'id': rental.id,
        'power_bank_id': rental.power_bank_id,
        'rent_time': rental.rent_time.isoformat(),
        'return_time': rental.return_time.isoformat() if rental.return_time else None,
        'status': rental.status
    } for rental in rentals]), 200

# Payment Endpoints
@app.route('/pay/<int:payment_id>', methods=['POST'])
@jwt_required()
def process_payment(payment_id):
    """Process payment for a rental."""
    current_user_id = get_jwt_identity()
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'message': 'Payment not found'}), 404
    
    rental = Rental.query.get(payment.rental_id)
    if rental.user_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    payment.status = 'completed'
    db.session.commit()
    
    return jsonify({'message': 'Payment processed successfully'}), 200

# Admin Endpoints
@app.route('/admin/stations', methods=['POST'])
@admin_required
def add_station():
    """Add a new station (admin only)."""
    data = request.get_json()
    name = data.get('name')
    location = data.get('location')
    
    if not name or not location:
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_station = Station(name=name, location=location)
    db.session.add(new_station)
    db.session.commit()
    
    return jsonify({'message': 'Station added successfully', 'station_id': new_station.id}), 201

@app.route('/admin/powerbanks', methods=['POST'])
@admin_required
def add_powerbank():
    """Add a new power bank to a station (admin only)."""
    data = request.get_json()
    station_id = data.get('station_id')
    
    if not station_id:
        return jsonify({'message': 'Missing station_id'}), 400
    
    station = Station.query.get(station_id)
    if not station:
        return jsonify({'message': 'Station not found'}), 404
    
    new_powerbank = PowerBank(station_id=station_id)
    db.session.add(new_powerbank)
    db.session.commit()
    
    return jsonify({'message': 'Power bank added successfully', 'powerbank_id': new_powerbank.id}), 201

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
