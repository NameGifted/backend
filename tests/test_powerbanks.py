import unittest
from run import create_app, db, User, Station, PowerBank
from flask import json
from werkzeug.security import generate_password_hash

class TestPowerBanks(unittest.TestCase):
    def setUp(self):
        """
        Set up the test client and initialize the in-memory database.
        """
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'JWT_SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """
        Tear down the database after each test.
        """
        with self.app.app_context():
            db.drop_all()

    def register_admin(self):
        """
        Helper method to register and log in an admin user.
        Returns the JWT token for the admin user.
        """
        with self.app.app_context():
            # Create an admin user
            admin = User(
                username='admin',
                password=generate_password_hash('adminpass'),
                email='admin@example.com',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        
        # Log in the admin user to get the token
        response = self.client.post('/login', json={'username': 'admin', 'password': 'adminpass'})
        return json.loads(response.data)['access_token']

    def test_get_powerbank(self):
        """
        Test retrieving a power bank by ID.
        """
        with self.app.app_context():
            # Create a station and a power bank
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            powerbank = PowerBank(station_id=station.id)
            db.session.add(powerbank)
            db.session.commit()
            powerbank_id = powerbank.id
        
        # Make a request to get the power bank details
        response = self.client.get(f'/powerbanks/{powerbank_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['station_id'], station.id)

    def test_add_powerbank(self):
        """
        Test adding a new power bank to a station (admin only).
        """
        # Register and log in as an admin to get the token
        token = self.register_admin()
        with self.app.app_context():
            # Create a station
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            station_id = station.id
        
        # Make a request to add a new power bank to the station
        response = self.client.post(
            '/admin/powerbanks',
            json={'station_id': station_id},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        
        # Verify that the power bank was added to the correct station
        with self.app.app_context():
            powerbank = PowerBank.query.get(data['powerbank_id'])
            self.assertEqual(powerbank.station_id, station_id)

if __name__ == '__main__':
    unittest.main()
