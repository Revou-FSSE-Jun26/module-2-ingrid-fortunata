# Active Flagging & User Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add status flagging (`is_active`) to User, Product, and Category entities, refactor the products routes to pull from the database, and add a user login endpoint supporting password checks and active status validation.

**Architecture:** We will update the database models and SQL schema files, run database migrations, change the product endpoints from hardcoded to database-driven filtering, add a `/users/login` endpoint verifying credentials (hashed and plaintext), and update seed data and tests.

**Tech Stack:** Python 3, Flask, SQLAlchemy, Alembic/Flask-Migrate, Werkzeug security utilities.

## Global Constraints
- Every model change must have a corresponding database migration.
- Serialized structures from `to_dict()` must include the new `is_active` field.
- Inactive products and products in inactive categories must be hidden from GET `/products` and GET `/products/<id>`.
- Inactive users must not be able to log in.

---

### Task 1: Update SQLAlchemy Models

**Files:**
- Modify: `app/models/user.py`
- Modify: `app/models/product.py`
- Modify: `app/models/category.py`

**Interfaces:**
- Produces: Updated schema models that contain `is_active` attributes.

- [ ] **Step 1: Update User Model**
  Modify `app/models/user.py` to add the `is_active` column and include it in `to_dict()`.
  ```python
  # Add:
  is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)
  
  # In to_dict():
  'is_active': self.is_active
  ```

- [ ] **Step 2: Update Product Model**
  Modify `app/models/product.py` to add the `is_active` column and include it in `to_dict()`.
  ```python
  # Add:
  is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)
  
  # In to_dict():
  'is_active': self.is_active
  ```

- [ ] **Step 3: Update Category Model**
  Modify `app/models/category.py` to add the `is_active` column and include it in `to_dict()`.
  ```python
  # Add:
  is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)
  
  # In to_dict():
  'is_active': self.is_active
  ```

- [ ] **Step 4: Commit**
  ```bash
  git add app/models/user.py app/models/product.py app/models/category.py
  git commit -m "feat: add is_active column to User, Product, Category models"
  ```

---

### Task 2: Schema definition & Flask-Migrate

**Files:**
- Modify: `queries/schema.sql`

- [ ] **Step 1: Update Schema SQL**
  Modify `queries/schema.sql` to add `is_active BOOLEAN DEFAULT TRUE NOT NULL` to the `users`, `categories`, and `products` table creation scripts.

- [ ] **Step 2: Generate Alembic migration**
  Run: `flask db migrate -m "add is_active to user product category"`
  Expected: A new migration file is created under `migrations/versions/`.

- [ ] **Step 3: Apply migration**
  Run: `flask db upgrade`
  Expected: Migration succeeds and updates the local PostgreSQL database schema.

- [ ] **Step 4: Commit**
  ```bash
  git add queries/schema.sql migrations/versions/*
  git commit -m "migration: add is_active fields to PostgreSQL database"
  ```

---

### Task 3: Refactor Product Routes to use database with active filter

**Files:**
- Modify: `app/routes/products.py`

**Interfaces:**
- Consumes: Database models `Product` and `Category`.

- [ ] **Step 1: Refactor GET `/products`**
  Modify `app/routes/products.py` to query the database, filter for active products with active categories (or no categories), and serialize.
  ```python
  from app.models.product import Product
  from app.models.category import Category

  @products_bp.route('/products', methods=['GET'])
  def get_all_products():
      products = Product.query.join(
          Category, Product.category_id == Category.id, isouter=True
      ).filter(
          Product.is_active == True,
          (Category.id == None) | (Category.is_active == True)
      ).all()
      return jsonify({
          "success": True,
          "data": [p.to_dict() for p in products],
          "count": len(products)
      }), 200
  ```

- [ ] **Step 2: Refactor GET `/products/<int:id>`**
  Modify `app/routes/products.py` to return the product only if active and category is active.
  ```python
  @products_bp.route('/products/<int:id>', methods=['GET'])
  def get_product_by_id(id):
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
      return jsonify({
          "success": True,
          "data": product.to_dict()
      }), 200
  ```

- [ ] **Step 3: Commit**
  ```bash
  git add app/routes/products.py
  git commit -m "feat: refactor products routes to use database and active filters"
  ```

---

### Task 4: Add Login Endpoint with validation and active checks

**Files:**
- Modify: `app/routes/users.py`

- [ ] **Step 1: Implement login endpoint**
  Add `/users/login` `POST` route to `app/routes/users.py`.
  ```python
  from werkzeug.security import check_password_hash

  @users_bp.route('/users/login', methods=['POST'])
  def login_user():
      data = request.get_json() or {}
      identity = data.get('username') or data.get('email')
      password = data.get('password')

      if not identity or not password:
          return jsonify({
              'success': False,
              'error': 'Validation Error',
              'message': 'username/email and password are required.'
          }), 400

      user = User.query.filter((User.username == identity) | (User.email == identity)).first()

      if not user:
          return jsonify({
              'success': False,
              'error': 'Unauthorized',
              'message': 'Invalid username/email or password.'
          }), 401

      is_password_correct = False
      if user.password_hash.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
          is_password_correct = check_password_hash(user.password_hash, password)
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

      return jsonify({
          'success': True,
          'message': 'Login successful',
          'data': user.to_dict()
      }), 200
  ```

- [ ] **Step 2: Commit**
  ```bash
  git add app/routes/users.py
  git commit -m "feat: add user login endpoint with credentials check and active status validation"
  ```

---

### Task 5: Seed Data Updates

**Files:**
- Modify: `queries/seed.sql`
- Modify: `app/seed_data.py`

- [ ] **Step 1: Update `queries/seed.sql`**
  Modify seed.sql to include `is_active` values (add active and inactive categories, products, and users to demonstrate functionality).

- [ ] **Step 2: Update `app/seed_data.py`**
  Modify `app/seed_data.py` to seed active/inactive users, products, categories.
  Example: Add a deactivated user (`is_active=False`) and product (`is_active=False`).

- [ ] **Step 3: Commit**
  ```bash
  git add queries/seed.sql app/seed_data.py
  git commit -m "seed: update seed data to include active and inactive records"
  ```

---

### Task 6: Unit Testing

**Files:**
- Create: `test/test_active_flagging_and_login.py`

- [ ] **Step 1: Write tests for active filtering & login**
  Write tests covering:
  - Filtering of inactive products / categories.
  - Successful user login (via username and email, plaintext and hashed).
  - Failed login with invalid credentials.
  - Blocked login for deactivated users.

- [ ] **Step 2: Run all unit tests**
  Run: `python -m unittest discover -s test`
  Expected: All tests pass.

- [ ] **Step 3: Commit**
  ```bash
  git add test/test_active_flagging_and_login.py
  git commit -m "test: add active flagging and login endpoint test suite"
  ```
