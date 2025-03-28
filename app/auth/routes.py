from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer
from .models import User, db

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request body:
        - username (str): The desired username
        - email (str): The user's email address
        - password (str): The user's password

    Returns:
        - 201: User created successfully
        - 400: Missing fields or username/email already exists
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Check for missing fields
    if not username or not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    # Hash the password and create a new user
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Log in a user and return access and refresh tokens.

    Request body:
        - identifier (str): Username or email
        - password (str): The user's password

    Returns:
        - 200: Access and refresh tokens
        - 401: Invalid credentials
    """
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')

    # Find user by username or email
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

    # Verify credentials
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh an access token using a refresh token.

    Requires a valid refresh token in the Authorization header.

    Returns:
        - 200: New access token
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_access_token}), 200

@auth_bp.route('/password/reset/request', methods=['POST'])
def password_reset_request():
    """
    Request a password reset token.

    Request body:
        - email (str): The user's email address

    Returns:
        - 200: Token generated (in practice, sent via email)
        - 404: Email not found
    """
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        s = URLSafeTimedSerializer('secret-key')  # Replace with app.config['SECRET_KEY'] in production
        token = s.dumps(user.id)
        # In a real application, send the token via email here
        return jsonify({"message": "Password reset token generated", "token": token}), 200
    else:
        return jsonify({"message": "Email not found"}), 404

@auth_bp.route('/password/reset', methods=['POST'])
def password_reset():
    """
    Reset a user's password using a reset token.

    Request body:
        - token (str): The password reset token
        - new_password (str): The new password

    Returns:
        - 200: Password reset successfully
        - 400: Invalid or expired token
        - 404: User not found
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    s = URLSafeTimedSerializer('secret-key')  # Replace with app.config['SECRET_KEY'] in production
    try:
        user_id = s.loads(token, max_age=3600)  # Token expires after 1 hour
        user = User.query.get(user_id)
        if user:
            hashed_password = generate_password_hash(new_password)
            user.password = hashed_password
            db.session.commit()
            return jsonify({"message": "Password reset successfully"}), 200
        else:
            return jsonify({"message": "User not found"}), 404
    except:
        return jsonify({"message": "Invalid or expired token"}), 400

@auth_bp.route('/password/change', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change the password of the authenticated user.

    Request body:
        - current_password (str): The current password
        - new_password (str): The new password

    Requires a valid access token in the Authorization header.

    Returns:
        - 200: Password changed successfully
        - 401: Invalid current password
    """
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user and check_password_hash(user.password, current_password):
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()
        return jsonify({"message": "Password changed successfully"}), 200
    else:
        return jsonify({"message": "Invalid current password"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """
    Get the authenticated user's details.

    Requires a valid access token in the Authorization header.

    Returns:
        - 200: User's username and email
        - 404: User not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        return jsonify({"username": user.username, "email": user.email}), 200
    else:
        return jsonify({"message": "User not found"}), 404
