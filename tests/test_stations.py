import unittest
from run import create_app, db, User, Station
from flask import json
from werkzeug.security import generate_password_hash

class TestStations(unittest.TestCase):
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

    def test_get_stations(self):
        with self.app.app_context():
            station1 = Station(name='Station 1', location='Location 1')
            station2 = Station(name='Station 2', location='Location 2')
            db.session.add_all([station1, station2])
            db.session.commit()
        response = self.client.get('/stations')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

    def test_get_station(self):
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            station_id = station.id
        response = self.client.get(f'/stations/{station_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Station 1')

    def test_add_station(self):
        token = self.register_admin()
        response = self.client.post(
            '/admin/stations',
            json={'name': 'New Station', 'location': 'New Location'},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        with self.app.app_context():
            station = Station.query.get(data['station_id'])
            self.assertEqual(station.name, 'New Station')

if __name__ == '__main__':
    unittest.main()
