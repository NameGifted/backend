import unittest
from run import create_app, db, User, Station, PowerBank
from flask import json
from werkzeug.security import generate_password_hash

class TestPowerBanks(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'JWT_SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def register_admin(self):
        with self.app.app_context():
            admin = User(
                username='admin',
                password=generate_password_hash('adminpass'),
                email='admin@example.com',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        response = self.client.post('/login', json={'username': 'admin', 'password': 'adminpass'})
        return json.loads(response.data)['access_token']

    def test_get_powerbank(self):
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            powerbank = PowerBank(station_id=station.id)
            db.session.add(powerbank)
            db.session.commit()
            powerbank_id = powerbank.id
        response = self.client.get(f'/powerbanks/{powerbank_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['station_id'], station.id)

    def test_add_powerbank(self):
        token = self.register_admin()
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            station_id = station.id
        response = self.client.post(
            '/admin/powerbanks',
            json={'station_id': station_id},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        with self.app.app_context():
            powerbank = PowerBank.query.get(data['powerbank_id'])
            self.assertEqual(powerbank.station_id, station_id)

if __name__ == '__main__':
    unittest.main()
