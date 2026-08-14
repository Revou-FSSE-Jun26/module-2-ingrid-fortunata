# RevoShop API Endpoints Design

This document details the architecture, schemas, and endpoint specifications for the implementation of User, Product, Category, and Order modules in RevoShop using Flask, SQLAlchemy, and Flask-JWT-Extended.

---

## 1. Authentication & Security Configuration
- **Library**: `Flask-JWT-Extended`
- **Token Type**: JWT (Access Token)
- **Expiration**: 1 day (`timedelta(days=1)`)
- **Identity Payload**: User ID as string (e.g. `"1"`)
- **Headers**: JWT is expected in the `Authorization: Bearer <token>` header for protected endpoints.
- **Custom Error Callbacks**: Registered on `JWTManager` to ensure standard JSON responses:
  - Expired: `401 Unauthorized` - `{"success": false, "error": "Unauthorized", "message": "The token has expired."}`
  - Invalid: `401 Unauthorized` - `{"success": false, "error": "Unauthorized", "message": "Signature verification failed."}`
  - Missing: `401 Unauthorized` - `{"success": false, "error": "Unauthorized", "message": "Missing Authorization Header."}`

---

## 2. Product Images Database Normalization & Optimization
To support product images without bloating the main `products` table and slowing down general queries, we normalize images into a separate database table:

### 2.1 Model: `ProductImage`
- `id`: Integer, primary key
- `product_id`: Integer, foreign key referencing `products.id` (with `ondelete='CASCADE'`)
- `image_base64`: Text, required (stores base64 string representation of the image)
- `is_primary`: Boolean, required (default `False`, flags if image is the primary preview image)
- `created_at`: DateTime, default current timestamp

### 2.2 Relationship
- In `Product`:
  `images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan', lazy=True)`

### 2.3 Optimization Strategy
- **List Route (`GET /products`)**: Utilizes a single optimized SQL outer join with a subquery filtering for only the image record where `is_primary == True`. It returns a single string property `primary_image` (Base64) or `null`.
- **Detail Route (`GET /products/<id>`)**: Returns the full details of the product, including a list of all images (`images` field) associated with the product.

### 2.4 Validation Rules
- **Count**: Maximum 3 images per product.
- **Primary Flag**: If images are provided, exactly one image must have `is_primary = True`. If none are marked primary, the first image is automatically set to primary. If more than one is marked primary, a `400 Bad Request` validation error is returned.
- **Size**: Individual Base64 strings should not exceed 1MB in length to prevent DB bloat.

---

## 3. Endpoint Specs

### 3.1 User & Authentication Module
* **`POST /users` (Register)**
  - Schema: `UserRegisterInputSchema`
  - Response: `UserRegisterResponseSchema` (201 Created)
* **`POST /auth/login` (Login)**
  - Schema: `UserLoginInputSchema`
  - Response: `UserLoginResponseSchema` (200 OK)
  - Returns access token: `{"success": true, "message": "Login successful", "data": {"token": "<JWT>", "user": { ... }}}`
  - *Note*: We keep `POST /users/login` as an alias/compatibility route for backward compatibility with Checkpoint 2 tests.

### 3.2 Product Module
* **`POST /products` (Create Product)**
  - Schema: `ProductCreateInputSchema` (includes `images` field consisting of a list of up to 3 `ProductImageInputSchema` objects)
  - Response: `ProductGetResponseSchema` (201 Created)
* **`GET /products` (List Products)**
  - Response: `ProductListResponseSchema` (200 OK)
  - Returns list of active products with active categories. Includes `primary_image` field.
* **`GET /products/<id>` (Get Product)**
  - Response: `ProductDetailResponseSchema` (200 OK)
  - Includes full list of associated `images`.
* **`PUT /products/<id>` (Update Product)**
  - Schema: `ProductUpdateInputSchema`
  - Response: `ProductDetailResponseSchema` (200 OK)
* **`DELETE /products/<id>` (Delete Product)**
  - Validation: Checks if product ID is linked to any entry in `order_items` table.
  - If linked: Blocks deletion and returns `400 Bad Request` with `{"success": false, "error": "Conflict", "message": "Cannot delete product because it is linked to existing orders."}`.
  - If not linked: Deletes product and returns `200 OK` with `{"success": true, "message": "Product deleted successfully"}`. Note that cascade deletion will clean up associated images.

### 3.3 Category Module
* **`POST /categories` (Create Category)**
  - Schema: `CategoryCreateInputSchema`
  - Response: `CategoryGetResponseSchema` (201 Created)
* **`GET /categories` (List Categories)**
  - Response: `CategoryListResponseSchema` (200 OK)
* **`GET /categories/<id>` (Get Category with products)**
  - Response: `CategoryWithProductsResponseSchema` (200 OK)
  - Includes a list of all products belonging to that category under the `products` field.
* **`PUT /categories/<id>` (Update Category)**
  - Schema: `CategoryUpdateInputSchema`
  - Response: `CategoryGetResponseSchema` (200 OK)
* **`DELETE /categories/<id>` (Delete Category)**
  - Deletes the category. Associated products will automatically have their `category_id` set to `NULL` (foreign key `ondelete='SET NULL'`).
  - Response: `200 OK`

### 3.4 Order Module (Protected by `@jwt_required()`)
* **`POST /orders` (Place Order)**
  - Schema: `OrderCreateInputSchema`
  - Items list validated: stock verified and deducted.
  - Inserts entries into `order_items` with quantity and purchase price.
  - Response: `OrderDetailResponseSchema` (201 Created)
* **`GET /orders` (List User Orders)**
  - Returns all orders for the current authenticated user.
  - Response: `OrderListResponseSchema` (200 OK)
* **`GET /orders/<id>` (Get Specific Order Details)**
  - Retrieves order detail, checking that the order belongs to the current user.
  - Queries `order_items` and joins with `products` to construct complete order items info.
  - Response: `OrderDetailResponseSchema` (200 OK)
* **`DELETE /orders/<id>` (Delete Order)**
  - Removes associated `order_items` first to satisfy the `RESTRICT` constraint, then removes the order record.
  - Response: `200 OK`

---

## 4. Data Validation Schemas
All input and response structures will be modeled using `marshmallow` schemas in `app/schemas/` to ensure schema validation is handled cleanly by Flask-Smorest.

---

## 5. Verification Plan
- **Unit Tests**:
  - Write test suite in `test/test_new_endpoints.py` covering success and failure states of each endpoint.
  - Test registration, JWT token generation, unauthorized/expired headers, CRUD on categories and products, product deletion safety, product images validation (count, primary flag, size), order placement stock deduction, order retrieval, and order deletion constraints.
- **Run verification command**:
  - `venv/bin/python -m unittest discover -s test`
