from app import db
from auth.models import User
from datetime import datetime

class Station(db.Model):
    """
    Represents a physical station where power banks are stored.
    """
    __tablename__ = 'station'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    powerbanks = db.relationship('PowerBank', backref='station', lazy=True)

    def to_dict(self):
        """
        Serializes the Station object to a dictionary.
        """
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location
        }

class PowerBank(db.Model):
    """
    Represents a power bank available for rental.
    """
    __tablename__ = 'powerbank'
    
    id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Integer, nullable=False)  # Capacity in mAh
    current_charge = db.Column(db.Integer, nullable=False)  # Current charge in mAh
    status = db.Column(db.String(20), default='available')  # e.g., 'available', 'rented', 'maintenance'
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    rentals = db.relationship('Rental', backref='powerbank', lazy=True)

    def rent(self, user_id):
        """
        Rents the power bank to a user by creating a Rental record and updating status.
        
        Args:
            user_id (int): The ID of the user renting the power bank.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if self.status != 'available':
            return False, "Power bank is not available"
        
        rental = Rental(
            powerbank_id=self.id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            status='active'
        )
        db.session.add(rental)
        self.status = 'rented'
        db.session.commit()
        return True, "Power bank rented successfully"

    def return_powerbank(self, current_charge):
        """
        Returns the power bank, updating its charge and ending the active rental.
        
        Args:
            current_charge (int): The remaining charge in mAh upon return.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        active_rental = Rental.query.filter_by(powerbank_id=self.id, status='active').first()
        if not active_rental:
            return False, "No active rental found"
        
        active_rental.end_time = datetime.utcnow()
        active_rental.status = 'completed'
        self.current_charge = current_charge
        self.status = 'available'
        db.session.commit()
        return True, "Power bank returned successfully"

    def to_dict(self):
        """
        Serializes the PowerBank object to a dictionary.
        """
        return {
            'id': self.id,
            'capacity': self.capacity,
            'current_charge': self.current_charge,
            'status': self.status,
            'station_id': self.station_id
        }

class Rental(db.Model):
    """
    Represents a rental transaction of a power bank by a user.
    """
    __tablename__ = 'rental'
    
    id = db.Column(db.Integer, primary_key=True)
    powerbank_id = db.Column(db.Integer, db.ForeignKey('powerbank.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)  # Null if rental is ongoing
    status = db.Column(db.String(20), default='active')  # e.g., 'active', 'completed'

    def to_dict(self):
        """
        Serializes the Rental object to a dictionary.
        """
        return {
            'id': self.id,
            'powerbank_id': self.powerbank_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status
        }
