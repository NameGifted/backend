import unittest
from run import create_app, db, User, Station, PowerBank, Rental, Payment
from flask import json
from werkzeug.security import generate_password_hash

class TestRentals(unittest.TestCase):
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

    def register_user(self, username, password, email):
        return self.client.post('/register', json={
            'username': username,
            'password': password,
            'email': email
        })

    def login_user(self, username, password):
        response = self.client.post('/login', json={'username': username, 'password': password})
        return json.loads(response.data)['access_token']

    def test_rent_powerbank(self):
        self.register_user('user1', 'password', 'user1@example.com')
        token = self.login_user('user1', 'password')
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            powerbank = PowerBank(station_id=station.id)
            db.session.add(powerbank)
            db.session.commit()
            powerbank_id = powerbank.id
        response = self.client.post(
            '/rent',
            json={'powerbank_id': powerbank_id},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        with self.app.app_context():
            powerbank = PowerBank.query.get(powerbank_id)
            self.assertEqual(powerbank.status, 'rented')

    def test_return_powerbank(self):
        self.register_user('user1', 'password', 'user1@example.com')
        token = self.login_user('user1', 'password')
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            db.session.add(station)
            db.session.commit()
            powerbank = PowerBank(station_id=station.id)
            db.session.add(powerbank)
            db.session.commit()
            rental = Rental(user_id=1, power_bank_id=powerbank.id)
            db.session.add(rental)
            db.session.commit()
            rental_id = rental.id
            powerbank.status = 'rented'
            db.session.commit()
        response = self.client.post(
            '/return',
            json={'rental_id': rental_id, 'station_id': station.id},
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            powerbank = PowerBank.query.get(powerbank.id)
            self.assertEqual(powerbank.status, 'available')

    def test_get_rentals(self):
        self.register_user('user1', 'password', 'user1@example.com')
        token = self.login_user('user1', 'password')
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            powerbank = PowerBank(station_id=station.id)
            rental = Rental(user_id=1, power_bank_id=powerbank.id)
            db.session.add_all([station, powerbank, rental])
            db.session.commit()
        response = self.client.get('/rentals', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)

    def test_process_payment(self):
        self.register_user('user1', 'password', 'user1@example.com')
        token = self.login_user('user1', 'password')
        with self.app.app_context():
            station = Station(name='Station 1', location='Location 1')
            powerbank = PowerBank(station_id=station.id)
            rental = Rental(user_id=1, power_bank_id=powerbank.id)
            payment = Payment(rental_id=rental.id, amount=10.0)
            db.session.add_all([station, powerbank, rental, payment])
            db.session.commit()
            payment_id = payment.id
        response = self.client.post(
            f'/pay/{payment_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            payment = Payment.query.get(payment_id)
            self.assertEqual(payment.status, 'completed')

if __name__ == '__main__':
    unittest.main()
