from flask import Flask
from .extensions import db, jwt
from .config import Config
from .auth.routes import auth_bp
from .stations.routes import stations_bp
from .powerbanks.routes import powerbanks_bp
from .rentals.routes import rentals_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(stations_bp, url_prefix='/stations')
    app.register_blueprint(powerbanks_bp, url_prefix='/powerbanks')
    app.register_blueprint(rentals_bp, url_prefix='/rentals')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
