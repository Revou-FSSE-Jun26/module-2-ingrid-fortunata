# RevoShop API Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the new User Authentication, Product CRUD (with Base64 product image uploads, limit of 3, and primary image flagging), Category CRUD, and Order CRUD modules with JWT authentication and stock validation.

**Architecture:** Integrate `Flask-JWT-Extended` for secure route authorization with custom JSON error handlers. Use Flask-Smorest for schema validation, route registration, and automatic documentation. Implement database transitions inside transactions using standard SQLAlchemy `db.session` operations. Optimize product listings by storing images in a normalized table and querying only the primary image via joined subquery.

**Tech Stack:** Python, Flask, Flask-SQLAlchemy, Flask-Smorest, Flask-JWT-Extended, Marshmallow.

## Global Constraints
- Naming conventions: snake_case for fields/variables.
- Error payloads must format to `{"success": false, "error": "<ErrorType>", "message": "<Detail>"}`.
- JWT tokens expire in exactly 1 day.

---

### Task 1: JWT Authentication & Configuration Setup

**Files:**
- Modify: [requirements.txt](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/requirements.txt)
- Modify: [app/extensions.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/extensions.py)
- Modify: [app/config.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/config.py)
- Modify: [app/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/__init__.py)

**Interfaces:**
- Produces: `jwt` instance in `app/extensions.py`

- [ ] **Step 1: Add Flask-JWT-Extended to requirements**
  Add the following line to `requirements.txt`:
  ```text
  Flask-JWT-Extended==4.6.0
  ```

- [ ] **Step 2: Install dependencies**
  Run: `venv/bin/pip install -r requirements.txt`
  Expected: Command runs successfully.

- [ ] **Step 3: Define configurations in config.py**
  Add JWT config keys in `app/config.py`:
  ```python
  from datetime import timedelta
  # inside Config class:
  JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
  JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
  ```

- [ ] **Step 4: Declare JWTManager in extensions.py**
  Add to `app/extensions.py`:
  ```python
  from flask_jwt_extended import JWTManager
  jwt = JWTManager()
  ```

- [ ] **Step 5: Setup Custom JWT error callbacks in extensions.py**
  Add to `app/extensions.py` to ensure standard JSON error structures:
  ```python
  @jwt.expired_token_loader
  def expired_token_callback(jwt_header, jwt_payload):
      return jsonify({
          "success": False,
          "error": "Unauthorized",
          "message": "The token has expired."
      }), 401

  @jwt.invalid_token_loader
  def invalid_token_callback(error):
      return jsonify({
          "success": False,
          "error": "Unauthorized",
          "message": "Signature verification failed."
      }), 401

  @jwt.unauthorized_loader
  def unauthorized_callback(error):
      return jsonify({
          "success": False,
          "error": "Unauthorized",
          "message": "Missing Authorization Header."
      }), 401
  ```

- [ ] **Step 6: Initialize JWT in app factory**
  In `app/__init__.py`, import `jwt` and call `jwt.init_app(flask_app)`:
  ```python
  from app.extensions import db, migrate, api, jwt
  # inside create_app:
  jwt.init_app(flask_app)
  ```

- [ ] **Step 7: Run existing test suite to ensure no regressions**
  Run: `venv/bin/python -m unittest discover -s test`
  Expected: All 16 tests pass.

- [ ] **Step 8: Commit changes**
  Run:
  ```bash
  git add requirements.txt app/extensions.py app/config.py app/__init__.py
  git commit -m "feat: configure Flask-JWT-Extended and custom error handlers"
  ```

---

### Task 2: Implement User Login with JWT

**Files:**
- Modify: [app/schemas/user.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/user.py)
- Modify: [app/schemas/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/__init__.py)
- Modify: [app/routes/users.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/routes/users.py)
- Create: `test/test_new_endpoints.py`

**Interfaces:**
- Produces: `POST /auth/login` endpoint

- [ ] **Step 1: Define login JWT response schemas**
  Add to `app/schemas/user.py`:
  ```python
  class AuthLoginResponseDataSchema(Schema):
      token = fields.Str(dump_only=True)
      user = fields.Nested(UserSchema, dump_only=True)

  class AuthLoginResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      message = fields.Str(dump_only=True)
      data = fields.Nested(AuthLoginResponseDataSchema, dump_only=True)
  ```

- [ ] **Step 2: Export new schemas**
  In `app/schemas/__init__.py`, import and export:
  ```python
  from app.schemas.user import (
      UserSchema,
      UserRegisterInputSchema,
      UserRegisterResponseSchema,
      UserLoginInputSchema,
      UserLoginResponseSchema,
      UserGetResponseSchema,
      AuthLoginResponseSchema,
  )
  ```

- [ ] **Step 3: Implement POST /auth/login in users.py**
  Add to `app/routes/users.py`:
  ```python
  from flask_jwt_extended import create_access_token
  from app.schemas import AuthLoginResponseSchema

  @users_bp.route('/auth/login', methods=['POST'])
  @users_bp.arguments(UserLoginInputSchema, location='json')
  @users_bp.response(200, AuthLoginResponseSchema)
  def login_auth(login_data):
      """Login endpoint returning JWT token expiring in 1 day."""
      from werkzeug.security import check_password_hash
      
      identity = login_data.get('username') or login_data.get('email')
      password = login_data.get('password')

      user = User.query.filter((User.username == identity) | (User.email == identity)).first()

      if not user:
          return jsonify({
              'success': False,
              'error': 'Unauthorized',
              'message': 'Invalid username/email or password.'
          }), 401

      is_password_correct = False
      if user.password_hash.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
          try:
              is_password_correct = check_password_hash(user.password_hash, password)
          except ValueError:
              is_password_correct = False
          
          if not is_password_correct:
              parts = user.password_hash.split(':')
              if len(parts) > 1 and parts[-1] == password:
                  is_password_correct = True
      else:
          is_password_correct = (user.password_hash == password)

      if not is_password_correct:
          return jsonify({
              'success': False,
              'error': 'Unauthorized',
              'message': 'Invalid username/email or password.'
          }), 401

      if not user.is_active:
          return jsonify({
              'success': False,
              'error': 'Forbidden',
              'message': 'Account is deactivated.'
          }), 403

      token = create_access_token(identity=str(user.id))
      return jsonify({
          'success': True,
          'message': 'Login successful',
          'data': {
              'token': token,
              'user': user.to_dict()
          }
      }), 200
  ```

- [ ] **Step 4: Create unit tests for POST /auth/login**
  Write initial tests in `test/test_new_endpoints.py`:
  ```python
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
  ```

- [ ] **Step 5: Run tests**
  Run: `venv/bin/python -m unittest test/test_new_endpoints.py`
  Expected: PASS

- [ ] **Step 6: Commit changes**
  Run:
  ```bash
  git add app/schemas/user.py app/schemas/__init__.py app/routes/users.py test/test_new_endpoints.py
  git commit -m "feat: implement POST /auth/login with JWT token response"
  ```

---

### Task 3: Product CRUD with Base64 Image Support

**Files:**
- Modify: [app/models/product.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/models/product.py)
- Modify: [app/models/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/models/__init__.py)
- Modify: [app/schemas/product.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/product.py)
- Modify: [app/schemas/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/__init__.py)
- Modify: [app/routes/products.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/routes/products.py)
- Modify: `test/test_new_endpoints.py`

**Interfaces:**
- Produces: `ProductImage` database model, DB migration, schemas for images, updated `GET /products` (with `primary_image`), `POST /products`, `PUT /products/<id>`, `DELETE /products/<id>` supporting images.

- [ ] **Step 1: Declare ProductImage model & update Product model**
  In `app/models/product.py`, add `ProductImage` class and relationship inside `Product`:
  ```python
  # inside app/models/product.py:
  class Product(db.Model):
      # ... existing fields ...
      images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan', lazy=True)

  class ProductImage(db.Model):
      __tablename__ = 'product_images'

      id = db.Column(db.Integer, primary_key=True)
      product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
      image_base64 = db.Column(db.Text, nullable=False)
      is_primary = db.Column(db.Boolean, default=False, nullable=False)
      created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

      def to_dict(self):
          return {
              'id': self.id,
              'image_base64': self.image_base64,
              'is_primary': self.is_primary,
              'created_at': self.created_at.isoformat() if self.created_at else None
          }
  ```

- [ ] **Step 2: Export model**
  In `app/models/__init__.py`, import and export `ProductImage`:
  ```python
  from app.models.product import Product, ProductImage
  # Add to __all__
  ```

- [ ] **Step 3: Generate and apply database migration**
  Run:
  ```bash
  venv/bin/flask db migrate -m "add product images table"
  venv/bin/flask db upgrade
  ```
  Expected: Migration succeeds and table `product_images` is created in PostgreSQL.

- [ ] **Step 4: Define image schemas & validation rules**
  In `app/schemas/product.py`, define input/output schemas for product images:
  ```python
  from marshmallow import validates, ValidationError, validates_schema

  class ProductImageSchema(Schema):
      id = fields.Int(dump_only=True)
      image_base64 = fields.Str(required=True)
      is_primary = fields.Bool()
      created_at = fields.DateTime(dump_only=True)

  class ProductImageInputSchema(Schema):
      image_base64 = fields.Str(required=True)
      is_primary = fields.Bool(load_default=False)

      @validates("image_base64")
      def validate_image_size(self, value):
          # Limit size to ~1MB (Base64 length ~1.37M chars)
          if len(value) > 1500000:
              raise ValidationError("Image size exceeds the 1MB limit.")

  class ProductCreateInputSchema(Schema):
      category_id = fields.Int(allow_none=True)
      name = fields.Str(required=True)
      description = fields.Str(allow_none=True)
      price = fields.Float(required=True)
      stock = fields.Int(required=True)
      is_active = fields.Bool(load_default=True)
      images = fields.List(fields.Nested(ProductImageInputSchema), load_default=list)

      @validates("price")
      def validate_price(self, value):
          if value <= 0:
              raise ValidationError("Price must be greater than zero.")

      @validates("stock")
      def validate_stock(self, value):
          if value < 0:
              raise ValidationError("Stock cannot be negative.")

      @validates_schema
      def validate_images(self, data, **kwargs):
          imgs = data.get("images", [])
          if len(imgs) > 3:
              raise ValidationError("A product can have at most 3 images.")
          
          # Count primaries
          primaries = sum(1 for img in imgs if img.get("is_primary"))
          if len(imgs) > 0 and primaries > 1:
              raise ValidationError("Exactly one image can be flagged as primary.")

  class ProductUpdateInputSchema(Schema):
      category_id = fields.Int(allow_none=True)
      name = fields.Str()
      description = fields.Str(allow_none=True)
      price = fields.Float()
      stock = fields.Int()
      is_active = fields.Bool()
      images = fields.List(fields.Nested(ProductImageInputSchema))

      @validates("price")
      def validate_price(self, value):
          if value <= 0:
              raise ValidationError("Price must be greater than zero.")

      @validates("stock")
      def validate_stock(self, value):
          if value < 0:
              raise ValidationError("Stock cannot be negative.")

      @validates_schema
      def validate_images(self, data, **kwargs):
          imgs = data.get("images")
          if imgs is not None:
              if len(imgs) > 3:
                  raise ValidationError("A product can have at most 3 images.")
              primaries = sum(1 for img in imgs if img.get("is_primary"))
              if len(imgs) > 0 and primaries > 1:
                  raise ValidationError("Exactly one image can be flagged as primary.")

  class ProductListSchema(ProductSchema):
      primary_image = fields.Str(dump_only=True)

  class ProductListResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.List(fields.Nested(ProductListSchema), dump_only=True)
      count = fields.Int(dump_only=True)

  class ProductDetailSchema(ProductSchema):
      images = fields.List(fields.Nested(ProductImageSchema), dump_only=True)

  class ProductDetailResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.Nested(ProductDetailSchema, dump_only=True)
  ```

- [ ] **Step 5: Export new product schemas**
  In `app/schemas/__init__.py`, update:
  ```python
  from app.schemas.product import (
      ProductSchema,
      ProductListResponseSchema,
      ProductGetResponseSchema,
      ProductCreateInputSchema,
      ProductUpdateInputSchema,
      ProductDetailResponseSchema,
  )
  ```

- [ ] **Step 6: Update GET /products (List) to fetch primary image**
  In `app/routes/products.py`, rewrite `get_all_products` to join with the primary image subquery:
  ```python
  @products_bp.route('/products', methods=['GET'])
  @products_bp.response(200, ProductListResponseSchema)
  def get_all_products():
      """Returns list of active products with their primary image."""
      # Subquery to select the base64 content of primary image
      primary_image_subquery = db.session.query(
          ProductImage.product_id,
          ProductImage.image_base64
      ).filter(
          ProductImage.is_primary == True
      ).subquery()

      # Query products joined with primary images
      products_query = db.session.query(
          Product,
          primary_image_subquery.c.image_base64.label('primary_image')
      ).join(
          Category, Product.category_id == Category.id, isouter=True
      ).outerjoin(
          primary_image_subquery, Product.id == primary_image_subquery.c.product_id
      ).filter(
          Product.is_active == True,
          (Category.id == None) | (Category.is_active == True)
      ).all()

      data = []
      for prod, primary_image in products_query:
          d = prod.to_dict()
          d['primary_image'] = primary_image
          data.append(d)

      return jsonify({
          "success": True,
          "data": data,
          "count": len(data)
      }), 200
  ```

- [ ] **Step 7: Implement POST, PUT, DELETE product and detail GET routes**
  In `app/routes/products.py`, add and update the endpoints:
  ```python
  from app.models.product import ProductImage
  from app.models.category import Category
  from app.models.order import order_items
  from app.schemas import ProductDetailResponseSchema

  @products_bp.route('/products', methods=['POST'])
  @products_bp.arguments(ProductCreateInputSchema, location='json')
  @products_bp.response(201, ProductDetailResponseSchema)
  def create_product(product_data):
      """Create a product with up to 3 images."""
      images_data = product_data.pop('images', [])

      if product_data.get('category_id'):
          if not db.session.get(Category, product_data['category_id']):
              return jsonify({
                  "success": False,
                  "error": "Validation Error",
                  "message": "Category not found."
              }), 400

      new_product = Product(**product_data)
      db.session.add(new_product)
      db.session.commit() # Save product first to get ID

      if images_data:
          # If no image is primary, default the first one to primary
          if not any(img.get('is_primary') for img in images_data):
              images_data[0]['is_primary'] = True

          for img_obj in images_data:
              new_img = ProductImage(
                  product_id=new_product.id,
                  image_base64=img_obj['image_base64'],
                  is_primary=img_obj.get('is_primary', False)
              )
              db.session.add(new_img)
          db.session.commit()

      # Build detail response
      prod_dict = new_product.to_dict()
      prod_dict['images'] = [img.to_dict() for img in new_product.images]

      return jsonify({
          "success": True,
          "message": "Product created successfully",
          "data": prod_dict
      }), 201

  @products_bp.route('/products/<int:id>', methods=['GET'])
  @products_bp.response(200, ProductDetailResponseSchema)
  def get_product_by_id(id):
      """Retrieves a single active product by ID along with all images."""
      product = Product.query.join(
          Category, Product.category_id == Category.id, isouter=True
      ).filter(
          Product.id == id,
          Product.is_active == True,
          (Category.id == None) | (Category.is_active == True)
      ).first()

      if not product:
          return jsonify({
              "success": False,
              "error": "Product not found",
              "message": f"No product exists with ID {id}"
          }), 404

      prod_dict = product.to_dict()
      prod_dict['images'] = [img.to_dict() for img in product.images]
      return jsonify({
          "success": True,
          "data": prod_dict
      }), 200

  @products_bp.route('/products/<int:id>', methods=['PUT'])
  @products_bp.arguments(ProductUpdateInputSchema, location='json')
  @products_bp.response(200, ProductDetailResponseSchema)
  def update_product(product_data, id):
      """Update a product and its images."""
      product = db.session.get(Product, id)
      if not product:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Product with ID {id} not found."
          }), 404

      if product_data.get('category_id'):
          if not db.session.get(Category, product_data['category_id']):
              return jsonify({
                  "success": False,
                  "error": "Validation Error",
                  "message": "Category not found."
              }), 400

      images_data = product_data.pop('images', None)

      # Update standard fields
      for key, val in product_data.items():
          setattr(product, key, val)
      db.session.commit()

      # Handle image replacement
      if images_data is not None:
          # Delete existing images first
          ProductImage.query.filter_by(product_id=id).delete()
          
          if images_data:
              if not any(img.get('is_primary') for img in images_data):
                  images_data[0]['is_primary'] = True

              for img_obj in images_data:
                  new_img = ProductImage(
                      product_id=id,
                      image_base64=img_obj['image_base64'],
                      is_primary=img_obj.get('is_primary', False)
                  )
                  db.session.add(new_img)
          db.session.commit()

      prod_dict = product.to_dict()
      prod_dict['images'] = [img.to_dict() for img in product.images]

      return jsonify({
          "success": True,
          "message": "Product updated successfully",
          "data": prod_dict
      }), 200

  @products_bp.route('/products/<int:id>', methods=['DELETE'])
  def delete_product(id):
      """Delete a product, blocked if linked to any orders."""
      product = db.session.get(Product, id)
      if not product:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Product with ID {id} not found."
          }), 404

      # Check if linked to any orders
      has_orders = db.session.query(order_items).filter_by(product_id=id).first() is not None
      if has_orders:
          return jsonify({
              "success": False,
              "error": "Conflict",
              "message": "Cannot delete product because it is linked to existing orders."
          }), 400

      # Deletion of product triggers Cascade deletion of associated images
      db.session.delete(product)
      db.session.commit()
      return jsonify({
          "success": True,
          "message": "Product deleted successfully"
      }), 200
  ```

- [ ] **Step 8: Create unit tests for product image CRUD & validation**
  Add to `test/test_new_endpoints.py`:
  ```python
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
  ```

- [ ] **Step 9: Run tests**
  Run: `venv/bin/python -m unittest test/test_new_endpoints.py`
  Expected: PASS

- [ ] **Step 10: Commit changes**
  Run:
  ```bash
  git add app/models/product.py app/models/__init__.py app/schemas/product.py app/schemas/__init__.py app/routes/products.py test/test_new_endpoints.py
  git commit -m "feat: implement product image uploads with size & count limits and joins optimization"
  ```

---

### Task 4: Implement Category CRUD Endpoints

**Files:**
- Create: `app/schemas/category.py`
- Create: `app/routes/categories.py`
- Modify: [app/schemas/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/__init__.py)
- Modify: [app/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/__init__.py)
- Modify: `test/test_new_endpoints.py`

**Interfaces:**
- Produces: `POST /categories`, `GET /categories`, `GET /categories/<id>`, `PUT /categories/<id>`, `DELETE /categories/<id>`

- [ ] **Step 1: Write Category schemas**
  Create `app/schemas/category.py`:
  ```python
  from marshmallow import Schema, fields
  from app.schemas.product import ProductSchema

  class CategorySchema(Schema):
      id = fields.Int(dump_only=True)
      name = fields.Str(required=True)
      description = fields.Str(allow_none=True)
      is_active = fields.Bool()
      created_at = fields.DateTime(dump_only=True)

  class CategoryWithProductsSchema(CategorySchema):
      products = fields.List(fields.Nested(ProductSchema), dump_only=True)

  class CategoryCreateInputSchema(Schema):
      name = fields.Str(required=True)
      description = fields.Str(allow_none=True)
      is_active = fields.Bool(load_default=True)

  class CategoryUpdateInputSchema(Schema):
      name = fields.Str()
      description = fields.Str(allow_none=True)
      is_active = fields.Bool()

  class CategoryGetResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.Nested(CategorySchema, dump_only=True)

  class CategoryWithProductsResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.Nested(CategoryWithProductsSchema, dump_only=True)

  class CategoryListResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.List(fields.Nested(CategorySchema), dump_only=True)
      count = fields.Int(dump_only=True)
  ```

- [ ] **Step 2: Export Category schemas**
  Update `app/schemas/__init__.py`:
  ```python
  from app.schemas.category import (
      CategorySchema,
      CategoryWithProductsSchema,
      CategoryCreateInputSchema,
      CategoryUpdateInputSchema,
      CategoryGetResponseSchema,
      CategoryWithProductsResponseSchema,
      CategoryListResponseSchema,
  )
  ```

- [ ] **Step 3: Implement Category routes**
  Create `app/routes/categories.py`:
  ```python
  from flask_smorest import Blueprint
  from flask import jsonify
  from app.extensions import db
  from app.models.category import Category
  from app.schemas import (
      CategoryCreateInputSchema,
      CategoryUpdateInputSchema,
      CategoryGetResponseSchema,
      CategoryWithProductsResponseSchema,
      CategoryListResponseSchema,
  )

  categories_bp = Blueprint('categories', __name__, description='Operations on categories')

  @categories_bp.route('/categories', methods=['POST'])
  @categories_bp.arguments(CategoryCreateInputSchema, location='json')
  @categories_bp.response(201, CategoryGetResponseSchema)
  def create_category(category_data):
      """Create a category."""
      name = category_data.get('name')
      if Category.query.filter_by(name=name).first():
          return jsonify({
              "success": False,
              "error": "Conflict",
              "message": "Category name already exists."
          }), 400

      new_cat = Category(**category_data)
      db.session.add(new_cat)
      db.session.commit()
      return jsonify({
          "success": True,
          "message": "Category created successfully",
          "data": new_cat.to_dict()
      }), 201

  @categories_bp.route('/categories', methods=['GET'])
  @categories_bp.response(200, CategoryListResponseSchema)
  def get_categories():
      """List all categories."""
      categories = Category.query.all()
      return jsonify({
          "success": True,
          "data": [c.to_dict() for c in categories],
          "count": len(categories)
      }), 200

  @categories_bp.route('/categories/<int:id>', methods=['GET'])
  @categories_bp.response(200, CategoryWithProductsResponseSchema)
  def get_category_by_id(id):
      """Get a specific category along with its products."""
      category = db.session.get(Category, id)
      if not category:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Category with ID {id} not found."
          }), 404

      # Build payload with products
      cat_dict = category.to_dict()
      cat_dict['products'] = [p.to_dict() for p in category.products]
      return jsonify({
          "success": True,
          "data": cat_dict
      }), 200

  @categories_bp.route('/categories/<int:id>', methods=['PUT'])
  @categories_bp.arguments(CategoryUpdateInputSchema, location='json')
  @categories_bp.response(200, CategoryGetResponseSchema)
  def update_category(category_data, id):
      """Update a category."""
      category = db.session.get(Category, id)
      if not category:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Category with ID {id} not found."
          }), 404

      name = category_data.get('name')
      if name and name != category.name:
          if Category.query.filter_by(name=name).first():
              return jsonify({
                  "success": False,
                  "error": "Conflict",
                  "message": "Category name already exists."
              }), 400

      for key, val in category_data.items():
          setattr(category, key, val)

      db.session.commit()
      return jsonify({
          "success": True,
          "message": "Category updated successfully",
          "data": category.to_dict()
      }), 200

  @categories_bp.route('/categories/<int:id>', methods=['DELETE'])
  def delete_category(id):
      """Delete a category."""
      category = db.session.get(Category, id)
      if not category:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Category with ID {id} not found."
          }), 404

      db.session.delete(category)
      db.session.commit()
      return jsonify({
          "success": True,
          "message": "Category deleted successfully"
      }), 200
  ```

- [ ] **Step 4: Register Category blueprint in app factory**
  In `app/__init__.py`, import and register the Blueprint:
  ```python
  from app.routes.categories import categories_bp
  # inside create_app:
  api.register_blueprint(categories_bp)
  ```

- [ ] **Step 5: Create unit tests for Category CRUD**
  Add to `test/test_new_endpoints.py`:
  ```python
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
  ```

- [ ] **Step 6: Run tests**
  Run: `venv/bin/python -m unittest test/test_new_endpoints.py`
  Expected: PASS

- [ ] **Step 7: Commit changes**
  Run:
  ```bash
  git add app/schemas/category.py app/routes/categories.py app/schemas/__init__.py app/__init__.py test/test_new_endpoints.py
  git commit -m "feat: implement Category CRUD module routes and validation schemas"
  ```

---

### Task 5: Implement Order CRUD Endpoints with JWT Protection

**Files:**
- Create: `app/schemas/order.py`
- Create: `app/routes/orders.py`
- Modify: [app/schemas/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/schemas/__init__.py)
- Modify: [app/__init__.py](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/__init__.py)
- Modify: `test/test_new_endpoints.py`

**Interfaces:**
- Consumes: JWT tokens generated by `POST /auth/login`
- Produces: `POST /orders`, `GET /orders`, `GET /orders/<id>`, `DELETE /orders/<id>`

- [ ] **Step 1: Write Order schemas**
  Create `app/schemas/order.py`:
  ```python
  from marshmallow import Schema, fields

  class OrderItemInputSchema(Schema):
      product_id = fields.Int(required=True)
      quantity = fields.Int(required=True)

  class OrderCreateInputSchema(Schema):
      items = fields.List(fields.Nested(OrderItemInputSchema), required=True)

  class OrderResponseSchema(Schema):
      id = fields.Int(dump_only=True)
      user_id = fields.Int(dump_only=True)
      total_amount = fields.Float(dump_only=True)
      status = fields.Str(dump_only=True)
      created_at = fields.DateTime(dump_only=True)
      updated_at = fields.DateTime(dump_only=True)

  class OrderDetailItemSchema(Schema):
      product_id = fields.Int()
      name = fields.Str()
      description = fields.Str()
      quantity = fields.Int()
      price_at_purchase = fields.Float()

  class OrderDetailSchema(OrderResponseSchema):
      items = fields.List(fields.Nested(OrderDetailItemSchema), dump_only=True)

  class OrderResponseWrapperSchema(Schema):
      success = fields.Bool(dump_only=True)
      message = fields.Str(dump_only=True)
      data = fields.Nested(OrderDetailSchema, dump_only=True)

  class OrderListResponseSchema(Schema):
      success = fields.Bool(dump_only=True)
      data = fields.List(fields.Nested(OrderResponseSchema), dump_only=True)
      count = fields.Int(dump_only=True)
  ```

- [ ] **Step 2: Export Order schemas**
  Update `app/schemas/__init__.py`:
  ```python
  from app.schemas.order import (
      OrderItemInputSchema,
      OrderCreateInputSchema,
      OrderResponseSchema,
      OrderResponseWrapperSchema,
      OrderListResponseSchema,
  )
  ```

- [ ] **Step 3: Implement Order routes**
  Create `app/routes/orders.py`:
  ```python
  from flask_smorest import Blueprint
  from flask import jsonify
  from flask_jwt_extended import jwt_required, get_jwt_identity
  from app.extensions import db
  from app.models.order import Order, order_items
  from app.models.product import Product
  from app.schemas import (
      OrderCreateInputSchema,
      OrderResponseWrapperSchema,
      OrderListResponseSchema,
  )

  orders_bp = Blueprint('orders', __name__, description='Operations on orders')

  @orders_bp.route('/orders', methods=['POST'])
  @jwt_required()
  @orders_bp.arguments(OrderCreateInputSchema, location='json')
  @orders_bp.response(201, OrderResponseWrapperSchema)
  def create_order(order_data):
      """Place a new order linked to the logged-in user."""
      user_id = int(get_jwt_identity())
      items = order_data.get('items', [])

      if not items:
          return jsonify({
              "success": False,
              "error": "Validation Error",
              "message": "Order must contain at least one item."
          }), 400

      total_amount = 0.00
      product_updates = []

      # Validate stock and compute totals
      for item in items:
          prod_id = item['product_id']
          qty = item['quantity']
          if qty <= 0:
              return jsonify({
                  "success": False,
                  "error": "Validation Error",
                  "message": "Quantity must be greater than zero."
              }), 400

          product = db.session.get(Product, prod_id)
          if not product or not product.is_active:
              return jsonify({
                  "success": False,
                  "error": "Not Found",
                  "message": f"Product with ID {prod_id} not found."
              }), 400

          if product.stock < qty:
              return jsonify({
                  "success": False,
                  "error": "Bad Request",
                  "message": f"Insufficient stock for product '{product.name}'."
              }), 400

          # Decrement stock
          product.stock -= qty
          total_amount += float(product.price) * qty
          product_updates.append((product, qty))

      # Create order
      new_order = Order(
          user_id=user_id,
          total_amount=total_amount,
          status='pending'
      )
      db.session.add(new_order)
      db.session.commit()

      # Write order_items values
      for product, qty in product_updates:
          stmt = order_items.insert().values(
              order_id=new_order.id,
              product_id=product.id,
              quantity=qty,
              price_at_purchase=product.price
          )
          db.session.execute(stmt)

      db.session.commit()

      # Get detailed representation
      detailed_items = []
      for product, qty in product_updates:
          detailed_items.append({
              "product_id": product.id,
              "name": product.name,
              "description": product.description,
              "quantity": qty,
              "price_at_purchase": float(product.price)
          })

      order_payload = new_order.to_dict()
      order_payload['items'] = detailed_items

      return jsonify({
          "success": True,
          "message": "Order placed successfully",
          "data": order_payload
      }), 201

  @orders_bp.route('/orders', methods=['GET'])
  @jwt_required()
  @orders_bp.response(200, OrderListResponseSchema)
  def get_orders():
      """List all orders for the current user."""
      user_id = int(get_jwt_identity())
      orders = Order.query.filter_by(user_id=user_id).all()
      return jsonify({
          "success": True,
          "data": [o.to_dict() for o in orders],
          "count": len(orders)
      }), 200

  @orders_bp.route('/orders/<int:id>', methods=['GET'])
  @jwt_required()
  @orders_bp.response(200, OrderResponseWrapperSchema)
  def get_order_by_id(id):
      """View a specific order with its order items and product details."""
      user_id = int(get_jwt_identity())
      order = db.session.get(Order, id)
      if not order or order.user_id != user_id:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Order with ID {id} not found."
          }), 404

      # Retrieve order items joined with product info
      items_query = db.session.query(
          order_items.c.product_id,
          order_items.c.quantity,
          order_items.c.price_at_purchase,
          Product.name,
          Product.description
      ).join(
          Product, order_items.c.product_id == Product.id
      ).filter(
          order_items.c.order_id == id
      ).all()

      detailed_items = []
      for row in items_query:
          detailed_items.append({
              "product_id": row.product_id,
              "name": row.name,
              "description": row.description,
              "quantity": row.quantity,
              "price_at_purchase": float(row.price_at_purchase)
          })

      order_payload = order.to_dict()
      order_payload['items'] = detailed_items

      return jsonify({
          "success": True,
          "data": order_payload
      }), 200

  @orders_bp.route('/orders/<int:id>', methods=['DELETE'])
  @jwt_required()
  def delete_order(id):
      """Delete an order, clearing foreign key restrictions in order_items first."""
      user_id = int(get_jwt_identity())
      order = db.session.get(Order, id)
      if not order or order.user_id != user_id:
          return jsonify({
              "success": False,
              "error": "Not Found",
              "message": f"Order with ID {id} not found."
          }), 404

      # Delete order_items first due to RESTRICT constraint
      db.session.execute(order_items.delete().where(order_items.c.order_id == id))
      db.session.delete(order)
      db.session.commit()

      return jsonify({
          "success": True,
          "message": "Order deleted successfully"
      }), 200
  ```

- [ ] **Step 4: Register Order blueprint in app factory**
  In `app/__init__.py`, import and register the Blueprint:
  ```python
  from app.routes.orders import orders_bp
  # inside create_app:
  api.register_blueprint(orders_bp)
  ```

- [ ] **Step 5: Create unit tests for Orders**
  Add to `test/test_new_endpoints.py`:
  ```python
      def test_order_lifecycle(self):
          # Login to get token
          payload = {"username": "alice_smith", "password": "hash_sample_alice"}
          res = self.client.post('/auth/login', json=payload)
          token = res.get_json()['data']['token']
          headers = {"Authorization": f"Bearer {token}"}

          # Verify unauthorized failure
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
  ```

- [ ] **Step 6: Run full test suite**
  Run: `venv/bin/python -m unittest discover -s test`
  Expected: All tests pass, including the original 16 tests and the new test suite.

- [ ] **Step 7: Commit changes**
  Run:
  ```bash
  git add app/schemas/order.py app/routes/orders.py app/schemas/__init__.py app/__init__.py test/test_new_endpoints.py
  git commit -m "feat: implement Order CRUD endpoints and stock validation with JWT protection"
  ```
