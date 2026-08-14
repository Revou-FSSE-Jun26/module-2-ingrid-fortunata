import unittest
import json
from app import create_app
from app.extensions import db
from app.models.user import User

class NewEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_auth_login_success(self):
        payload = {"username": "alice_smith", "password": "hash_sample_alice"}
        response = self.client.post('/auth/login', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['username'], "alice_smith")

    def test_product_crud(self):
        # Test create validation fail (negative price)
        bad_payload = {"name": "Broken", "price": -5, "stock": 10}
        res = self.client.post('/products', json=bad_payload)
        self.assertEqual(res.status_code, 400)

        # Test create success
        payload = {"name": "New Gaming Mouse", "price": 49.99, "stock": 20}
        res = self.client.post('/products', json=payload)
        self.assertEqual(res.status_code, 201)
        prod_id = res.get_json()['data']['id']

        # Test update
        up_payload = {"price": 39.99}
        res = self.client.put(f'/products/{prod_id}', json=up_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['price'], 39.99)

        # Test delete success
        res = self.client.delete(f'/products/{prod_id}')
        self.assertEqual(res.status_code, 200)

        # Test delete block (linked to order seed data)
        res = self.client.delete('/products/1') # Product ID 1 is linked to seeded orders
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['success'])

    def test_product_images_crud_and_validation(self):
        # Test validation - over 3 images
        bad_payload = {
            "name": "Broken Mouse",
            "price": 10.00,
            "stock": 5,
            "images": [
                {"image_base64": "img1"},
                {"image_base64": "img2"},
                {"image_base64": "img3"},
                {"image_base64": "img4"}
            ]
        }
        res = self.client.post('/products', json=bad_payload)
        self.assertEqual(res.status_code, 400)

        # Test validation - size limit
        huge_payload = {
            "name": "Broken Mouse",
            "price": 10.00,
            "stock": 5,
            "images": [{"image_base64": "a" * 2000000}]
        }
        res = self.client.post('/products', json=huge_payload)
        self.assertEqual(res.status_code, 400)

        # Test validation - multiple primary flags
        double_primary_payload = {
            "name": "Double Mouse",
            "price": 10.00,
            "stock": 5,
            "images": [
                {"image_base64": "img1", "is_primary": True},
                {"image_base64": "img2", "is_primary": True}
            ]
        }
        res = self.client.post('/products', json=double_primary_payload)
        self.assertEqual(res.status_code, 400)

        # Test create success - defaults first to primary
        success_payload = {
            "name": "Camera",
            "price": 350.00,
            "stock": 10,
            "images": [
                {"image_base64": "base64_data_1"},
                {"image_base64": "base64_data_2"}
            ]
        }
        res = self.client.post('/products', json=success_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()['data']
        prod_id = data['id']
        self.assertEqual(len(data['images']), 2)
        # First image automatically set to is_primary = True
        self.assertTrue(data['images'][0]['is_primary'])
        self.assertFalse(data['images'][1]['is_primary'])

        # Test GET list contains primary_image
        res_list = self.client.get('/products')
        self.assertEqual(res_list.status_code, 200)
        found = [p for p in res_list.get_json()['data'] if p['id'] == prod_id]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['primary_image'], "base64_data_1")

        # Cleanup
        self.client.delete(f'/products/{prod_id}')

    def test_category_crud(self):
        # Test create success
        payload = {"name": "Kitchenware", "description": "Kitchen items"}
        res = self.client.post('/categories', json=payload)
        self.assertEqual(res.status_code, 201)
        cat_id = res.get_json()['data']['id']

        # Test list
        res = self.client.get('/categories')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.get_json()['count'], 1)

        # Test get single with products
        res = self.client.get(f'/categories/{cat_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('products', res.get_json()['data'])

        # Test update
        res = self.client.put(f'/categories/{cat_id}', json={"name": "Kitchenware Upgraded"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['name'], "Kitchenware Upgraded")

        # Test delete
        res = self.client.delete(f'/categories/{cat_id}')
        self.assertEqual(res.status_code, 200)

    def test_order_lifecycle(self):
        # Login to get token
        payload = {"username": "alice_smith", "password": "hash_sample_alice"}
        res = self.client.post('/auth/login', json=payload)
        token = res.get_json()['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        # Verify unauthorized failure (no token)
        res_unauth = self.client.post('/orders', json={"items": []})
        self.assertEqual(res_unauth.status_code, 401)

        # Get product to verify stock
        from app.models.product import Product
        prod = Product.query.filter_by(name="Organic Cotton Hoodie").first()
        self.assertIsNotNone(prod)
        initial_stock = prod.stock

        # Place order
        order_payload = {"items": [{"product_id": prod.id, "quantity": 2}]}
        res = self.client.post('/orders', json=order_payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        
        order_data = res.get_json()['data']
        order_id = order_data['id']
        self.assertEqual(order_data['items'][0]['quantity'], 2)

        # Verify stock decrement
        db.session.refresh(prod)
        self.assertEqual(prod.stock, initial_stock - 2)

        # Get order list
        res = self.client.get('/orders', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.get_json()['count'], 1)

        # Get specific order details
        res = self.client.get(f'/orders/{order_id}', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()['data']['items']), 1)

        # Delete order
        res = self.client.delete(f'/orders/{order_id}', headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_user_registration_password_hashing(self):
        # Register new user with raw password
        register_payload = {
            "username": "hashed_user",
            "email": "hashed@example.com",
            "password": "raw_secret_password"
        }
        res = self.client.post('/users', json=register_payload)
        self.assertEqual(res.status_code, 201)

        # Retrieve user from DB and check password_hash is not plain text
        user = User.query.filter_by(username="hashed_user").first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, "raw_secret_password")
        self.assertTrue(user.password_hash.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')))

        # Cleanup
        db.session.delete(user)
        db.session.commit()

    def test_order_item_quantity_validations(self):
        payload = {"username": "alice_smith", "password": "hash_sample_alice"}
        res = self.client.post('/auth/login', json=payload)
        token = res.get_json()['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        # Test quantity zero or negative
        bad_payload = {"items": [{"product_id": 1, "quantity": 0}]}
        res = self.client.post('/orders', json=bad_payload, headers=headers)
        self.assertEqual(res.status_code, 400)

        bad_payload_neg = {"items": [{"product_id": 1, "quantity": -5}]}
        res = self.client.post('/orders', json=bad_payload_neg, headers=headers)
        self.assertEqual(res.status_code, 400)

if __name__ == '__main__':
    unittest.main()
