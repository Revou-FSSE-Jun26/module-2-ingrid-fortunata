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

    def _get_admin_headers(self):
        payload = {"username": "admin_user", "password": "admin_password"}
        res = self.client.post('/auth/login', json=payload)
        token = res.get_json()['data']['token']
        return {"Authorization": f"Bearer {token}"}

    def _get_customer_headers(self):
        payload = {"username": "alice_smith", "password": "alice_password"}
        res = self.client.post('/auth/login', json=payload)
        token = res.get_json()['data']['token']
        return {"Authorization": f"Bearer {token}"}

    def test_auth_login_success(self):
        payload = {"username": "alice_smith", "password": "alice_password"}
        response = self.client.post('/auth/login', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data['data'])
        self.assertEqual(data['data']['user']['username'], "alice_smith")

    def test_product_crud(self):
        headers = self._get_admin_headers()

        # Test create validation fail (negative price)
        bad_payload = {"name": "Broken", "price": -5, "stock": 10, "color": "Black"}
        res = self.client.post('/products', json=bad_payload, headers=headers)
        self.assertEqual(res.status_code, 400)

        # Test create validation fail (missing color)
        bad_payload_no_color = {"name": "No Color Shirt", "price": 19.90, "stock": 10}
        res = self.client.post('/products', json=bad_payload_no_color, headers=headers)
        self.assertEqual(res.status_code, 400)

        # Test create success with defaults (size -> Free Size, gender -> Unisex, auto SKU)
        payload = {"name": "Unisex Shoulder Bag", "price": 24.90, "stock": 50, "color": "Olive"}
        res = self.client.post('/products', json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        prod_data = res.get_json()['data']
        prod_id = prod_data['id']
        self.assertEqual(prod_data['size'], "Free Size")
        self.assertEqual(prod_data['gender'], "Unisex")
        self.assertEqual(prod_data['color'], "Olive")
        self.assertTrue(prod_data['sku'].startswith("UQ-"))

        # Test update
        up_payload = {"price": 29.90, "color": "Navy"}
        res = self.client.put(f'/products/{prod_id}', json=up_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['price'], 29.90)
        self.assertEqual(res.get_json()['data']['color'], "Navy")

        # Test delete success
        res = self.client.delete(f'/products/{prod_id}', headers=headers)
        self.assertEqual(res.status_code, 204)

        # Test delete blocked (linked to order seed data)
        res = self.client.delete('/products/1', headers=headers)  # Product ID 1 is linked to seeded orders
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.get_json()['error_code'], 'PRODUCT_CONFLICT')

    def test_product_images_crud_and_validation(self):
        headers = self._get_admin_headers()

        # Test validation - over 3 images
        bad_payload = {
            "name": "Broken Mouse",
            "price": 10.00,
            "stock": 5,
            "color": "Black",
            "images": [
                {"image_base64": "img1"},
                {"image_base64": "img2"},
                {"image_base64": "img3"},
                {"image_base64": "img4"}
            ]
        }
        res = self.client.post('/products', json=bad_payload, headers=headers)
        self.assertEqual(res.status_code, 400)

        # Test validation - size limit
        huge_payload = {
            "name": "Broken Mouse",
            "price": 10.00,
            "stock": 5,
            "color": "Black",
            "images": [{"image_base64": "a" * 2000000}]
        }
        res = self.client.post('/products', json=huge_payload, headers=headers)
        self.assertEqual(res.status_code, 400)

        # Test validation - multiple primary flags
        double_primary_payload = {
            "name": "Double Mouse",
            "price": 10.00,
            "stock": 5,
            "color": "Black",
            "images": [
                {"image_base64": "img1", "is_primary": True},
                {"image_base64": "img2", "is_primary": True}
            ]
        }
        res = self.client.post('/products', json=double_primary_payload, headers=headers)
        self.assertEqual(res.status_code, 400)

        # Test create success - defaults first to primary
        success_payload = {
            "name": "Camera Bag",
            "price": 35.00,
            "stock": 10,
            "color": "Black",
            "images": [
                {"image_base64": "base64_data_1"},
                {"image_base64": "base64_data_2"}
            ]
        }
        res = self.client.post('/products', json=success_payload, headers=headers)
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
        self.client.delete(f'/products/{prod_id}', headers=headers)

    def test_category_crud(self):
        headers = self._get_admin_headers()

        # Test create success
        payload = {"name": "Kitchenware", "description": "Kitchen items"}
        res = self.client.post('/categories', json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        cat_id = res.get_json()['data']['id']

        # Test list
        res = self.client.get('/categories')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.get_json()['data']), 1)

        # Test get single with products
        res = self.client.get(f'/categories/{cat_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('products', res.get_json()['data'])

        # Test update
        res = self.client.put(f'/categories/{cat_id}', json={"name": "Kitchenware Upgraded"}, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['name'], "Kitchenware Upgraded")

        # Test delete
        res = self.client.delete(f'/categories/{cat_id}', headers=headers)
        self.assertEqual(res.status_code, 204)

    def test_order_lifecycle(self):
        # Login to get token
        payload = {"username": "alice_smith", "password": "alice_password"}
        res = self.client.post('/auth/login', json=payload)
        token = res.get_json()['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        # Verify unauthorized failure (no token)
        res_unauth = self.client.post('/orders', json={"items": []})
        self.assertEqual(res_unauth.status_code, 401)

        # Get product to verify stock
        from app.models.product import Product
        prod = Product.query.filter_by(is_active=True).first()
        self.assertIsNotNone(prod)
        initial_stock = prod.stock

        # Place order (now requires shipping details, items sync size and color from product)
        order_payload = {
            "items": [{"product_id": prod.id, "quantity": 2}],
            "shipping_address": "Jl. Sudirman No.1, Jakarta",
            "recipient_name": "Alice Smith",
            "recipient_phone": "08123456789"
        }
        res = self.client.post('/orders', json=order_payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        
        order_data = res.get_json()['data']
        order_id = order_data['id']
        self.assertEqual(order_data['items'][0]['quantity'], 2)
        # Verify size and color are synced from product
        self.assertEqual(order_data['items'][0]['size'], prod.size)
        self.assertEqual(order_data['items'][0]['color'], prod.color)
        # Verify shipping fields are returned
        self.assertEqual(order_data['shipping_address'], "Jl. Sudirman No.1, Jakarta")
        self.assertEqual(order_data['recipient_name'], "Alice Smith")
        self.assertEqual(order_data['recipient_phone'], "08123456789")

        # Verify stock decrement
        db.session.refresh(prod)
        self.assertEqual(prod.stock, initial_stock - 2)

        # Get order list
        res = self.client.get('/orders', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.get_json()['data']), 1)

        # Get specific order details
        res = self.client.get(f'/orders/{order_id}', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()['data']['items']), 1)

        # Soft-cancel order (DELETE now returns 200 and preserves history)
        res = self.client.delete(f'/orders/{order_id}', headers=headers)
        self.assertEqual(res.status_code, 200)
        cancelled = res.get_json()['data']
        self.assertEqual(cancelled['status'], 'cancelled')

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
        payload = {"username": "alice_smith", "password": "alice_password"}
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

    def test_rbac_denied_for_customer(self):
        headers = self._get_customer_headers()

        # Test create category denied
        payload = {"name": "Blocked Category"}
        res = self.client.post('/categories', json=payload, headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()['error_code'], 'FORBIDDEN')

        # Test create product denied
        payload = {"name": "Blocked Product", "price": 10.00, "stock": 5}
        res = self.client.post('/products', json=payload, headers=headers)
        self.assertEqual(res.status_code, 403)

    def test_role_based_order_visibility_and_deletion(self):
        # 1. Admin logs in
        admin_headers = self._get_admin_headers()
        # 2. Customer logs in
        customer_headers = self._get_customer_headers()

        # 3. Customer places an order (now requires shipping details)
        order_payload = {
            "items": [{"product_id": 3, "quantity": 1}],
            "shipping_address": "Jl. Thamrin No.5, Jakarta",
            "recipient_name": "Alice Smith",
            "recipient_phone": "08111222333"
        }
        res = self.client.post('/orders', json=order_payload, headers=customer_headers)
        self.assertEqual(res.status_code, 201)
        order_id = res.get_json()['data']['id']

        # 4. Admin lists all orders — should be able to see the customer's order
        res_list = self.client.get('/orders', headers=admin_headers)
        self.assertEqual(res_list.status_code, 200)
        order_ids = [o['id'] for o in res_list.get_json()['data']]
        self.assertIn(order_id, order_ids)

        # 5. Admin retrieves the specific order details — should be allowed
        res_detail = self.client.get(f'/orders/{order_id}', headers=admin_headers)
        self.assertEqual(res_detail.status_code, 200)

        # 6. Another customer logs in and tries to view it — should get 404
        # Register a second customer
        reg_payload = {"username": "customer_two", "email": "two@example.com", "password": "password_two"}
        self.client.post('/users', json=reg_payload)
        login_res = self.client.post('/auth/login', json={"username": "customer_two", "password": "password_two"})
        other_token = login_res.get_json()['data']['token']
        other_headers = {"Authorization": f"Bearer {other_token}"}

        res_forbidden_get = self.client.get(f'/orders/{order_id}', headers=other_headers)
        self.assertEqual(res_forbidden_get.status_code, 404)

        # 7. Other customer tries to cancel it — should get 404
        res_forbidden_del = self.client.delete(f'/orders/{order_id}', headers=other_headers)
        self.assertEqual(res_forbidden_del.status_code, 404)

        # 8. Admin soft-cancels the order — should succeed (returns 200 with cancelled order)
        res_delete = self.client.delete(f'/orders/{order_id}', headers=admin_headers)
        self.assertEqual(res_delete.status_code, 200)
        self.assertEqual(res_delete.get_json()['data']['status'], 'cancelled')

        # Cleanup other customer
        user_two = User.query.filter_by(username="customer_two").first()
        if user_two:
            db.session.delete(user_two)
            db.session.commit()

    def test_fashion_adjustments_and_role_restrictions(self):
        admin_headers = self._get_admin_headers()
        customer_headers = self._get_customer_headers()

        # 1. Test user registration with invalid 'seller' role gets rejected
        reg_seller = {
            "username": "seller_candidate",
            "email": "seller_candidate@example.com",
            "password": "password123",
            "role": "seller"
        }
        res_seller = self.client.post('/users', json=reg_seller)
        self.assertIn(res_seller.status_code, [400, 422])  # Marshmallow schema validation error

        # 2. Test product creation: Size defaults to Free Size, Gender to Unisex, SKU auto-generated
        bag_payload = {
            "name": "Canvas Tote Bag",
            "description": "Minimalist everyday tote bag",
            "price": 19.90,
            "stock": 40,
            "color": "Natural Beige"
            # size, gender, sku omitted intentionally
        }
        res_bag = self.client.post('/products', json=bag_payload, headers=admin_headers)
        self.assertEqual(res_bag.status_code, 201)
        bag_data = res_bag.get_json()['data']
        bag_id = bag_data['id']
        self.assertEqual(bag_data['size'], "Free Size")
        self.assertEqual(bag_data['gender'], "Unisex")
        self.assertEqual(bag_data['color'], "Natural Beige")
        self.assertTrue(bag_data['sku'].startswith("UQ-"))

        # 3. Test order creation without shipping details gets rejected
        order_missing_shipping = {
            "items": [{"product_id": bag_id, "quantity": 1}],
            "shipping_address": "",  # Empty
            "recipient_name": "Alice",
            "recipient_phone": "0812345678"
        }
        res_bad_order = self.client.post('/orders', json=order_missing_shipping, headers=customer_headers)
        self.assertIn(res_bad_order.status_code, [400, 422])

        # 4. Test order creation: Item inherits size and color from product
        order_valid = {
            "items": [{"product_id": bag_id, "quantity": 1}],
            "shipping_address": "Jl. Senopati No. 20, Jakarta",
            "recipient_name": "Alice Smith",
            "recipient_phone": "081298765432"
        }
        res_order = self.client.post('/orders', json=order_valid, headers=customer_headers)
        self.assertEqual(res_order.status_code, 201)
        created_order = res_order.get_json()['data']
        self.assertEqual(created_order['shipping_address'], "Jl. Senopati No. 20, Jakarta")
        self.assertEqual(created_order['recipient_name'], "Alice Smith")
        self.assertEqual(created_order['recipient_phone'], "081298765432")
        self.assertEqual(created_order['items'][0]['size'], "Free Size")
        self.assertEqual(created_order['items'][0]['color'], "Natural Beige")

        # Cleanup created product and order
        from app.models.order import Order
        ord_obj = db.session.get(Order, created_order['id'])
        if ord_obj:
            db.session.delete(ord_obj)
            db.session.commit()
        self.client.delete(f'/products/{bag_id}', headers=admin_headers)

if __name__ == '__main__':
    unittest.main()


