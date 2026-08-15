import unittest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category

class ActiveFlaggingAndLoginTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_get_all_products_excludes_inactive(self):
        """GET /products should only return active products in active categories."""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
    def test_01_get_all_products_excludes_inactive(self):
        """GET /products should only return active products in active categories."""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify that only active products are in the list
        product_names = [p['name'] for p in data['data']]
        
        # 'Wireless Noise-Canceling Headphones' should be returned (active product, active category)
        self.assertIn('Wireless Noise-Canceling Headphones', product_names)
        
        # 'Deactivated Phone' should not be returned (inactive product)
        self.assertNotIn('Deactivated Phone', product_names)
        
        # 'Product in Inactive Category' should not be returned (active product but inactive category)
        self.assertNotIn('Product in Inactive Category', product_names)

    def test_02_get_product_by_id_active_check(self):
        """GET /products/<id> should return 404 for inactive products or products in inactive categories."""
        # Find active product
        active_prod = Product.query.filter_by(name='Wireless Noise-Canceling Headphones').first()
        self.assertIsNotNone(active_prod)
        response = self.client.get(f'/products/{active_prod.id}')
        self.assertEqual(response.status_code, 200)

        # Find inactive product
        inactive_prod = Product.query.filter_by(name='Deactivated Phone').first()
        self.assertIsNotNone(inactive_prod)
        response = self.client.get(f'/products/{inactive_prod.id}')
        self.assertEqual(response.status_code, 404)

        # Find product in inactive category
        prod_in_inactive_cat = Product.query.filter_by(name='Product in Inactive Category').first()
        self.assertIsNotNone(prod_in_inactive_cat)
        response = self.client.get(f'/products/{prod_in_inactive_cat.id}')
        self.assertEqual(response.status_code, 404)

    def test_03_login_validation_errors(self):
        """POST /auth/login should return 400 when identity or password is missing."""
        # Missing password
        response = self.client.post(
            '/auth/login',
            data=json.dumps({"username": "alice_smith"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

        # Missing identity
        response = self.client.post(
            '/auth/login',
            data=json.dumps({"password": "password"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_04_login_success_username(self):
        """POST /auth/login succeeds using username (hashed password check)."""
        payload = {
            "username": "alice_smith",
            "password": "alice_password"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['username'], "alice_smith")
        self.assertTrue(data['data']['user']['is_active'])

    def test_05_login_success_email(self):
        """POST /auth/login succeeds using email (hashed password check)."""
        payload = {
            "email": "alice@example.com",
            "password": "alice_password"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['username'], "alice_smith")

    def test_06_login_success_plaintext_fallback(self):
        """POST /auth/login succeeds with plaintext password fallback if hash check is skipped."""
        # Create a temp user with plaintext password
        plaintext_user = User(
            username="plain_user",
            email="plain@example.com",
            password_hash="plain_secret_pwd",
            is_active=True
        )
        db.session.add(plaintext_user)
        db.session.commit()

        payload = {
            "username": "plain_user",
            "password": "plain_secret_pwd"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['username'], "plain_user")

        # Cleanup
        db.session.delete(plaintext_user)
        db.session.commit()

    def test_07_login_failed_invalid_credentials(self):
        """POST /auth/login fails with 401 on wrong username/password."""
        # Wrong password
        payload = {
            "username": "alice_smith",
            "password": "wrong_password"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

        # Non-existent user
        payload = {
            "username": "no_such_user",
            "password": "any_password"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_08_login_failed_deactivated_user(self):
        """POST /auth/login fails with 403 Forbidden for deactivated users."""
        payload = {
            "username": "deactivated_user",
            "password": "deactivated_password"
        }
        response = self.client.post(
            '/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data['error_code'], 'USER_FORBIDDEN')
        self.assertEqual(data['message'], 'Account is deactivated.')

if __name__ == '__main__':
    unittest.main()
