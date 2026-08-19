import unittest
import json
from app import create_app
from app.extensions import db
from app.models.user import User

class Checkpoint2TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_get_all_products_hardcoded(self):
        """GET /products returning hardcoded JSON list using jsonify()"""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        print("\n--- GET /products Output ---")
        print(json.dumps(data, indent=2))
        self.assertGreaterEqual(len(data['data']), 2)

    def test_02_get_product_by_id_success(self):
        """GET /products/1 returning single product JSON"""
        response = self.client.get('/products/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        print("\n--- GET /products/1 Output ---")
        print(json.dumps(data, indent=2))
        self.assertEqual(data['data']['id'], 1)

    def test_03_get_product_by_id_not_found(self):
        """GET /products/999 returning 404 Not Found JSON"""
        response = self.client.get('/products/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        print("\n--- GET /products/999 (Not Found) Output ---")
        print(json.dumps(data, indent=2))
        self.assertEqual(data['error_code'], 'PRODUCT_NOT_FOUND')

    def test_04_post_user_register(self):
        """POST /users creating a User — uses 'password' field (schema hashes it internally)."""
        new_user_payload = {
            "username": "bob_builder",
            "email": "bob@example.com",
            "password": "secret_bob_pw"
        }
        
        # Clean up if exists from previous runs
        existing = User.query.filter_by(username="bob_builder").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        response = self.client.post(
            '/users',
            data=json.dumps(new_user_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        print("\n--- POST /users (Register) Output ---")
        print(json.dumps(data, indent=2))
        self.assertEqual(data['data']['username'], "bob_builder")
        self.assertIn('role', data['data'])

    def test_05_get_user_by_id_success(self):
        """GET /users/<id> retrieving user from DB (requires JWT auth)"""
        user = User.query.filter_by(username="bob_builder").first()
        self.assertIsNotNone(user)

        # Login as bob_builder to get token
        login_res = self.client.post('/auth/login', json={"username": "bob_builder", "password": "secret_bob_pw"})
        token = login_res.get_json()['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.get(f'/users/{user.id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        print(f"\n--- GET /users/{user.id} (Retrieve) Output ---")
        print(json.dumps(data, indent=2))
        self.assertEqual(data['data']['username'], "bob_builder")

    def test_06_get_user_by_id_not_found(self):
        """GET /users/9999 without token now returns 401 (auth required)"""
        response = self.client.get('/users/9999')
        self.assertEqual(response.status_code, 401)
        print("\n--- GET /users/9999 (No Token) Output ---")
        print(json.dumps(response.get_json(), indent=2))

if __name__ == '__main__':
    unittest.main()
