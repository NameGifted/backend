import unittest
from run import create_app, db
from flask import json

class TestAuth(unittest.TestCase):
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

    def test_register(self):
        """
        Test user registration endpoint.
        """
        response = self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'User registered successfully')

    def test_login(self):
        """
        Test user login endpoint.
        """
        # Register a user first
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com'
        })
        # Attempt to log in with the registered user's credentials
        response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)

    def test_profile(self):
        """
        Test profile retrieval endpoint.
        """
        # Register and log in to get the access token
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass',
            'email': 'test@example.com'
        })
        login_response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        token = json.loads(login_response.data)['access_token']
        # Access the profile endpoint with the token
        response = self.client.get('/profile', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], 'testuser')

if __name__ == '__main__':
    unittest.main()
