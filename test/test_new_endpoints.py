import unittest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product

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

        # Test create validation fail (negative price) - schema returns 422
        bad_payload = {"name": "Broken", "price": -5, "stock": 10, "color": "Black"}
        res = self.client.post('/products', json=bad_payload, headers=headers)
        self.assertEqual(res.status_code, 422)

        # Test create validation fail (missing color) - schema returns 422
        bad_payload_no_color = {"name": "No Color Shirt", "price": 19.90, "stock": 10}
        res = self.client.post('/products', json=bad_payload_no_color, headers=headers)
        self.assertEqual(res.status_code, 422)

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

        # Test validation - over 3 images (schema validation = 422)
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
        self.assertEqual(res.status_code, 422)

        # Test validation - size limit (schema validation = 422)
        huge_payload = {
            "name": "Broken Mouse",
            "price": 10.00,
            "stock": 5,
            "color": "Black",
            "images": [{"image_base64": "a" * 2000000}]
        }
        res = self.client.post('/products', json=huge_payload, headers=headers)
        self.assertEqual(res.status_code, 422)

        # Test validation - multiple primary flags (schema validation = 422)
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
        self.assertEqual(res.status_code, 422)

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

        # Test quantity zero or negative (schema validation = 422)
        bad_payload = {"items": [{"product_id": 1, "quantity": 0}]}
        res = self.client.post('/orders', json=bad_payload, headers=headers)
        self.assertEqual(res.status_code, 422)

        bad_payload_neg = {"items": [{"product_id": 1, "quantity": -5}]}
        res = self.client.post('/orders', json=bad_payload_neg, headers=headers)
        self.assertEqual(res.status_code, 422)

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

    def test_duplicate_order_items_validation_and_multi_products(self):
        """Test that duplicate product_id in items returns 422, while distinct products succeed."""
        customer_headers = self._get_customer_headers()

        # 1. Duplicate product_id 1 in items -> rejected with 422
        dup_payload = {
            "items": [
                {"product_id": 1, "quantity": 1},
                {"product_id": 1, "quantity": 2}
            ],
            "shipping_address": "Jl. Sudirman No. 1, Jakarta",
            "recipient_name": "Alice Smith",
            "recipient_phone": "+62 812-3456-7890"
        }
        res = self.client.post('/orders', json=dup_payload, headers=customer_headers)
        self.assertEqual(res.status_code, 422)
        err = res.get_json()
        self.assertEqual(err['error_code'], 'VALIDATION_ERROR')

        # 2. Distinct products (product_id: 1 and product_id: 2) -> succeeds with 201
        multi_payload = {
            "items": [
                {"product_id": 1, "quantity": 1},
                {"product_id": 2, "quantity": 1}
            ],
            "shipping_address": "Jl. Sudirman No. 1, Jakarta",
            "recipient_name": "Alice Smith",
            "recipient_phone": "+62 812-3456-7890"
        }
        res_multi = self.client.post('/orders', json=multi_payload, headers=customer_headers)
        self.assertEqual(res_multi.status_code, 201)
        created = res_multi.get_json()['data']
        self.assertEqual(len(created['items']), 2)

        # Cleanup created test order
        self.client.delete(f"/orders/{created['id']}", headers=customer_headers)

    def test_product_deletion_active_vs_completed_order_policy(self):
        """Test that active orders block product deletion (409), while finished orders allow soft-delete (204)."""
        admin_headers = self._get_admin_headers()
        customer_headers = self._get_customer_headers()

        # 1. Create a temporary product
        create_res = self.client.post('/products', json={
            "name": "Smart Delete Test Shirt",
            "price": 25.50,
            "stock": 100,
            "color": "Gray"
        }, headers=admin_headers)
        self.assertEqual(create_res.status_code, 201)
        test_prod_id = create_res.get_json()['data']['id']

        # 2. Place an order on this product (status: 'pending' -> ACTIVE)
        order_res = self.client.post('/orders', json={
            "items": [{"product_id": test_prod_id, "quantity": 1}],
            "shipping_address": "Jl. Merdeka No. 10, Jakarta",
            "recipient_name": "Test Recipient",
            "recipient_phone": "+62 811-2233-4455"
        }, headers=customer_headers)
        self.assertEqual(order_res.status_code, 201)
        test_order_id = order_res.get_json()['data']['id']

        # 3. Attempt to delete product while order is ACTIVE -> blocked with 409
        del_active_res = self.client.delete(f'/products/{test_prod_id}', headers=admin_headers)
        self.assertEqual(del_active_res.status_code, 409)
        self.assertEqual(del_active_res.get_json()['error_code'], 'PRODUCT_CONFLICT')

        # 4. Cancel the order (status becomes 'cancelled' -> FINISHED)
        cancel_res = self.client.delete(f'/orders/{test_order_id}', headers=customer_headers)
        self.assertEqual(cancel_res.status_code, 200)

        # 5. Now delete product -> succeeds with 204 (soft-deleted / deactivated)
        del_finished_res = self.client.delete(f'/products/{test_prod_id}', headers=admin_headers)
        self.assertEqual(del_finished_res.status_code, 204)

        # Verify product is soft-deleted (is_active = False)
        from app.models.product import Product
        prod_in_db = db.session.get(Product, test_prod_id)
        self.assertIsNotNone(prod_in_db)
        self.assertFalse(prod_in_db.is_active)

        # 6. Unordered product hard-delete test
        create_res2 = self.client.post('/products', json={
            "name": "Hard Delete Product",
            "price": 10.00,
            "stock": 10,
            "color": "Green"
        }, headers=admin_headers)
        self.assertEqual(create_res2.status_code, 201)
        test_prod_id2 = create_res2.get_json()['data']['id']

        del_hard_res = self.client.delete(f'/products/{test_prod_id2}', headers=admin_headers)
        self.assertEqual(del_hard_res.status_code, 204)
        self.assertIsNone(db.session.get(Product, test_prod_id2))

    def test_product_category_price_and_sort_filters(self):
        """Test GET /products filtering by category_id, min_price, max_price, and sorting."""
        # 1. Category ID filter
        res_cat = self.client.get('/products?category_id=1')
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.get_json()['data']
        for p in data_cat:
            self.assertEqual(p['category_id'], 1)

        # 2. Price range filter
        res_price = self.client.get('/products?min_price=10.00&max_price=20.00')
        self.assertEqual(res_price.status_code, 200)
        data_price = res_price.get_json()['data']
        for p in data_price:
            self.assertTrue(10.00 <= p['price'] <= 20.00)

        # 3. Sort by price ascending
        res_sort_asc = self.client.get('/products?sort_by=price_asc')
        self.assertEqual(res_sort_asc.status_code, 200)
        data_sort_asc = res_sort_asc.get_json()['data']
        prices_asc = [p['price'] for p in data_sort_asc]
        self.assertEqual(prices_asc, sorted(prices_asc))

        # 4. Sort by price descending
        res_sort_desc = self.client.get('/products?sort_by=price_desc')
        self.assertEqual(res_sort_desc.status_code, 200)
        data_sort_desc = res_sort_desc.get_json()['data']
        prices_desc = [p['price'] for p in data_sort_desc]
        self.assertEqual(prices_desc, sorted(prices_desc, reverse=True))

        # 5. Sort by oldest (updated_at ascending)
        res_sort_oldest = self.client.get('/products?sort_by=oldest')
        self.assertEqual(res_sort_oldest.status_code, 200)
        data_sort_oldest = res_sort_oldest.get_json()['data']
        dates_oldest = [p['updated_at'] for p in data_sort_oldest]
        self.assertEqual(dates_oldest, sorted(dates_oldest))

        # 6. Categories listed alphabetically
        res_cats = self.client.get('/categories')
        self.assertEqual(res_cats.status_code, 200)
        cat_names = [c['name'] for c in res_cats.get_json()['data']]
        self.assertEqual(cat_names, sorted(cat_names))

    def test_orders_status_filter(self):
        """Test GET /orders filtering by status and categorized search tracking."""
        customer_headers = self._get_customer_headers()

        # 1. Get orders filtered by status 'pending'
        res_pending = self.client.get('/orders?status=pending', headers=customer_headers)
        self.assertEqual(res_pending.status_code, 200)
        for order in res_pending.get_json()['data']:
            self.assertEqual(order['status'], 'pending')

        # 2. Get orders filtered by status 'delivered'
        res_delivered = self.client.get('/orders?status=delivered', headers=customer_headers)
        self.assertEqual(res_delivered.status_code, 200)
        for order in res_delivered.get_json()['data']:
            self.assertEqual(order['status'], 'delivered')

        # 3. Categorized search: recipient_name
        res_name_search = self.client.get('/orders?recipient_name=Alice', headers=customer_headers)
        self.assertEqual(res_name_search.status_code, 200)
        for order in res_name_search.get_json()['data']:
            self.assertIn('alice', order['recipient_name'].lower())

        # 4. General search: phone or address
        res_gen_search = self.client.get('/orders?search=Sudirman', headers=customer_headers)
        self.assertEqual(res_gen_search.status_code, 200)
        for order in res_gen_search.get_json()['data']:
            self.assertIn('sudirman', order['shipping_address'].lower())

    def test_role_aware_active_inactive_visibility(self):
        """Test that customers see only active categories/products, while admins see all / can filter."""
        admin_headers = self._get_admin_headers()
        customer_headers = self._get_customer_headers()

        # 1. Customer GET /categories -> only active
        res_cust_cats = self.client.get('/categories', headers=customer_headers)
        self.assertEqual(res_cust_cats.status_code, 200)
        for cat in res_cust_cats.get_json()['data']:
            self.assertTrue(cat['is_active'])

        # 2. Admin GET /categories -> shows all by default
        res_admin_cats = self.client.get('/categories', headers=admin_headers)
        self.assertEqual(res_admin_cats.status_code, 200)
        admin_cat_ids = [c['id'] for c in res_admin_cats.get_json()['data']]
        # Inactive category from seed data should be present in admin list
        inactive_cat = Category.query.filter_by(is_active=False).first()
        if inactive_cat:
            self.assertIn(inactive_cat.id, admin_cat_ids)

        # 3. Customer GET /products -> only active products
        res_cust_prods = self.client.get('/products', headers=customer_headers)
        self.assertEqual(res_cust_prods.status_code, 200)
        for prod in res_cust_prods.get_json()['data']:
            self.assertTrue(prod['is_active'])

        # 4. Admin GET /products?is_active=false -> returns inactive products
        res_admin_inactive = self.client.get('/products?is_active=false', headers=admin_headers)
        self.assertEqual(res_admin_inactive.status_code, 200)
        inactive_prods = res_admin_inactive.get_json()['data']
        for prod in inactive_prods:
            self.assertFalse(prod['is_active'])


if __name__ == '__main__':
    unittest.main()





