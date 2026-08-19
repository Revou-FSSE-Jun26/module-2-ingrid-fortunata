[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoFashion API — Online Clothing Store Backend

## Overview

**RevoFashion** is a fashion-focused e-commerce backend API inspired by **Uniqlo**, built using **Flask** and **PostgreSQL**. It exposes a RESTful JSON API that handles user registration & authentication, fashion clothing product catalog with attributes (`size`, `color`, `material`, `gender`, `sku`), category management, query filtering, and order placement with variant tracking and stock control.

The project is built progressively across bi-weekly checkpoints, covering **Checkpoint 1** (database design) and **Checkpoint 2** (Flask + SQLAlchemy layer with full API endpoints).

---

## Features Implemented

- ✅ PostgreSQL schema with 6 tables (`users`, `categories`, `products`, `product_images`, `orders`, `order_items`) with proper foreign key constraints
- ✅ Fashion-specific product attributes: `size` (XS–XXL, FREE), `color`, `material`, `gender` (Men, Women, Unisex, Kids), and unique `sku`
- ✅ Query filtering on `GET /products` by `gender`, `size`, `color`, and `material`
- ✅ Fashion order item variant tracking (`size` and `color` stored in `order_items` at purchase time)
- ✅ Flask application factory pattern with environment-based configuration
- ✅ SQLAlchemy ORM models for all entities (`User`, `Category`, `Product`, `ProductImage`, `Order`, `order_items`)
- ✅ Flask-Migrate (Alembic) for version-controlled schema migrations
- ✅ Flask-JWT-Extended for stateless JWT authentication (tokens expire in 1 day)
- ✅ Role-based access control (RBAC) via a custom `@roles_required` decorator
- ✅ Password hashing with Werkzeug's `generate_password_hash`
- ✅ Many-to-many relationship between `orders` and `products` via the `order_items` association table
- ✅ Product image support (base64-encoded, up to 3 images per product, one primary)
- ✅ Stock decrement on order creation with validation guard
- ✅ Stock restoration when an order is cancelled
- ✅ Order status lifecycle enforcement with role-based transition rules
- ✅ Swagger / OpenAPI 3.0 interactive documentation via Flask-Smorest
- ✅ Consistent JSON error response structure across all endpoints

---

## Technologies Used

| Technology         | Version | Purpose                                 |
| :----------------- | :------ | :-------------------------------------- |
| Python             | 3.x     | Core language                           |
| Flask              | 3.0.3   | Web framework                           |
| Flask-SQLAlchemy   | 3.1.1   | ORM layer                               |
| Flask-Migrate      | 4.0.7   | Database migration management (Alembic) |
| Flask-Smorest      | 0.47.0  | OpenAPI 3.0 / Swagger UI generation     |
| Flask-JWT-Extended | 4.6.0   | JWT authentication                      |
| marshmallow        | 4.3.1   | Request/response schema validation      |
| Werkzeug           | 3.1.8   | Password hashing utilities              |
| psycopg2-binary    | 2.9.12  | PostgreSQL database driver              |
| python-dotenv      | 1.0.1   | Environment variable management         |

---

## Project Architecture & Structure

```
module-2-ingrid-fortunata/
├── app/
│   ├── __init__.py           # Flask app factory; registers all blueprints & extensions
│   ├── auth.py               # roles_required() decorator for RBAC
│   ├── config.py             # Config class; DATABASE_URL, JWT, OpenAPI settings
│   ├── extensions.py         # SQLAlchemy, Migrate, CustomApi, JWTManager instances
│   ├── models/
│   │   ├── __init__.py       # Re-exports all models for migration discovery
│   │   ├── user.py           # User model (id, username, email, password_hash, role, is_active, created_at)
│   │   ├── category.py       # Category model
│   │   ├── product.py        # Product model & ProductImage model
│   │   └── order.py          # Order model + order_items association table (db.Table)
│   ├── routes/
│   │   ├── products.py       # GET, POST, PUT, DELETE /products
│   │   ├── users.py          # POST /users, GET /users/<id>, POST /auth/login
│   │   ├── categories.py     # GET, POST, PUT, DELETE /categories
│   │   └── orders.py         # GET, POST, PATCH, DELETE /orders
│   ├── schemas/
│   │   ├── __init__.py       # Re-exports all marshmallow schemas
│   │   ├── user.py           # UserRegisterInputSchema, UserGetResponseSchema, etc.
│   │   ├── product.py        # ProductCreateInputSchema, ProductDetailResponseSchema, etc.
│   │   ├── category.py       # CategoryCreateInputSchema, CategoryListResponseSchema, etc.
│   │   └── order.py          # OrderCreateInputSchema, OrderResponseWrapperSchema, etc.
│   └── seed_data.py          # Seeds sample categories, products, user, and order
├── migrations/               # Flask-Migrate / Alembic migration history
├── test/
│   └── test_new_endpoints.py # Automated test suite
├── img/                      # Checkpoint image evidence screenshots
├── queries/                  # Raw SQL queries for verification
├── .env                      # Local environment config (git-ignored)
├── .env.example              # Template for environment variables
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point (python3 run.py)
```

---

## How to Run the Project Locally

### Prerequisites

- Python 3.x
- PostgreSQL (running locally)
- A `revoshop_db` database already created

### Step-by-Step

**1. Clone the repository and create the database:**

```sql
-- In psql or pgAdmin
CREATE DATABASE revoshop_db;
```

**2. Set up the virtual environment and install dependencies:**

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables:**

Copy `.env.example` to `.env` and fill in your local values:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/revoshop_db
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
```

**4. Apply database migrations:**

```bash
flask db upgrade
```

> Migration history includes:
>
> - Initial migration: base tables (`users`, `categories`, `products`, `orders`, `order_items`)
> - Revision `aa0fd34ebf0e`: adds the `role` column to `users` without affecting existing rows

**5. (Optional) Seed sample data:**

```bash
PYTHONPATH=. python3 app/seed_data.py
```

Inserts sample categories, products, a user (`alice_smith`), and an order with multiple products through the `order_items` association table.

**6. Start the development server:**

```bash
python3 run.py
```

The API will be available at: **`http://127.0.0.1:5000`**

**7. (Optional) Run the automated test suite (still on progress):**

```bash
PYTHONPATH=. python3 -m pytest test/
```

---

## Swagger / OpenAPI Documentation

Interactive API documentation is auto-generated by **Flask-Smorest** and is available at:

> **`http://127.0.0.1:5000/swagger-ui`**

The OpenAPI 3.0 spec (JSON) is served at:

> **`http://127.0.0.1:5000/openapi.json`**

All request and response bodies are validated and documented via **marshmallow schemas**. Authentication-required endpoints are marked with a Bearer token security scheme in the Swagger UI.

---

## Role List

The `role` column on the `users` table controls access to protected endpoints via the `@roles_required` decorator.

| Role         | Description                                                       |
| :----------- | :---------------------------------------------------------------- |
| `superadmin` | Full access to all endpoints including management operations      |
| `admin`      | Can manage products, categories, and view all orders              |
| `seller`     | Can create/update/delete products and view all orders             |
| `customer`   | Can register, login, place orders, and view only their own orders |

> **Default role**: New users registered via `POST /users` default to `customer`.

---

## Order Status

The `status` column on the `orders` table tracks the lifecycle of an order.

| Status        | Description                                                             |
| :------------ | :---------------------------------------------------------------------- |
| `pending`     | Order placed, awaiting payment (default on creation)                    |
| `paid`        | Customer has completed payment                                          |
| `processing`  | Seller/admin is preparing the order                                     |
| `shipped`     | Order has been dispatched                                               |
| `delivered`   | Order successfully received by the customer                             |
| `cancelled`   | Order was cancelled (only from `pending` or `paid`)                     |

### Status Transition Rules

Status can only move **forward** according to this flow:

```
pending ──→ paid ──→ processing ──→ shipped ──→ delivered
   │           │
   └───────────┴──────────────────────────────→ cancelled
```

| From \ To     | `paid` | `processing` | `shipped` | `delivered` | `cancelled` |
| :------------ | :----: | :----------: | :-------: | :---------: | :---------: |
| `pending`     | ✅      | ❌            | ❌         | ❌           | ✅           |
| `paid`        | ❌      | ✅ *          | ❌         | ❌           | ✅           |
| `processing`  | ❌      | ❌            | ✅ *       | ❌           | ❌           |
| `shipped`     | ❌      | ❌            | ❌         | ✅ *         | ❌           |
| `delivered`   | —      | —            | —         | —           | —           |
| `cancelled`   | —      | —            | —         | —           | —           |

> \* Admin / Seller / Superadmin only. Customers can only trigger: `pending → paid`, `pending → cancelled`, `paid → cancelled`.

> **Cancellation & stock**: When an order is cancelled, all product stock quantities are automatically restored.

---

## API Endpoints

### Authentication

| Method | Endpoint      | Auth | Description                                             |
| :----- | :------------ | :--- | :------------------------------------------------------ |
| `POST` | `/auth/login` | None | Login with username/email + password; returns JWT token |

### Users

| Method | Endpoint      | Auth | Description                                       |
| :----- | :------------ | :--- | :------------------------------------------------ |
| `POST` | `/users`      | None | Register a new user; defaults role to `customer`  |
| `GET`  | `/users/<id>` | None | Retrieve a user by ID; returns `404` if not found |

### Products

| Method   | Endpoint         | Auth Required                   | Description                                    |
| :------- | :--------------- | :------------------------------ | :--------------------------------------------- |
| `GET`    | `/products`      | None                            | List active products (supports `?gender=`, `?size=`, `?color=`, `?material=`, `?page=`, `?per_page=`) |
| `GET`    | `/products/<id>` | None                            | Get a single active product with all images and fashion attributes |
| `POST`   | `/products`      | `superadmin`, `admin`, `seller` | Create a new clothing product with fashion attributes (`size`, `color`, `material`, `gender`, `sku`) and images |
| `PUT`    | `/products/<id>` | `superadmin`, `admin`, `seller` | Update a product and replace its images/fashion attributes |
| `DELETE` | `/products/<id>` | `superadmin`, `admin`, `seller` | Delete a product (blocked if linked to orders) |

### Categories

| Method   | Endpoint           | Auth Required                   | Description                                 |
| :------- | :----------------- | :------------------------------ | :------------------------------------------ |
| `GET`    | `/categories`      | None                            | List all categories                         |
| `GET`    | `/categories/<id>` | None                            | Get a category by ID including its products |
| `POST`   | `/categories`      | `superadmin`, `admin`, `seller` | Create a new category                       |
| `PUT`    | `/categories/<id>` | `superadmin`, `admin`, `seller` | Update a category                           |
| `DELETE` | `/categories/<id>` | `superadmin`, `admin`, `seller` | Delete a category                           |

### Orders

| Method   | Endpoint        | Auth Required     | Description                                                                 |
| :------- | :-------------- | :---------------- | :-------------------------------------------------------------------------- |
| `GET`    | `/orders`       | All authenticated | Admins/sellers see all orders; customers see only their own                 |
| `GET`    | `/orders/<id>`  | All authenticated | View order detail with items; customers restricted to their own orders      |
| `POST`   | `/orders`       | All authenticated | Place a new order; validates stock and decrements on success                |
| `PATCH`  | `/orders/<id>`  | All authenticated | Update order status following the lifecycle rules (see Status Transitions)  |
| `DELETE` | `/orders/<id>`  | All authenticated | Cancel an order (only `pending`/`paid`); restores product stock             |

---

### 📝 PUT Endpoint Convention: Full Object Replacement

Following standard REST architectural constraints, the **`PUT`** HTTP method represents a **full replacement** of the target resource. When issuing a `PUT` request, the client should send the complete state of the object in the request body.

#### Example 1: `PUT /products/<id>` (Full Body Payload)
```json
{
  "category_id": 1,
  "name": "AIRism Cotton Oversized Crew Neck T-Shirt",
  "description": "Upgraded AIRism cotton blend with relaxed silhouette and moisture-wicking technology.",
  "price": 19.90,
  "stock": 150,
  "size": "L",
  "color": "Navy",
  "material": "58% Cotton, 38% Polyester, 4% Spandex",
  "gender": "Men",
  "sku": "RF-TS-001-L",
  "is_active": true,
  "images": [
    {
      "image_base64": "data:image/jpeg;base64,...",
      "is_primary": true
    }
  ]
}
```

#### Example 2: `PUT /categories/<id>` (Full Body Payload)
```json
{
  "name": "T-Shirts & Tops",
  "description": "Everyday casual tees, graphic shirts, and tank tops.",
  "is_active": true
}
```

---

## Checkpoint 1: Database Design (Updated)

This checkpoint focuses on the initial PostgreSQL schema and seed data.

### Database Schema Overview

The database consists of 6 tables:

- `users` — Stores user account records
- `categories` — Product categories
- `products` — Store items, linked to a category
- `product_images` — Stores images for products
- `orders` — Orders placed by a user
- `order_items` — Junction table linking `orders` and `products` (many-to-many)

#### Database Schema Diagram

![Database Schema Diagram](./img/diagram2.png)

---

## Checkpoint 2: Flask & SQLAlchemy Layer

This checkpoint stands up the full Flask application layer with SQLAlchemy ORM, Flask-Migrate schema history, JWT auth, RBAC, and all REST API endpoints.

### Image Evidence

#### 1. GET /products — List all active products

![GET /products](./img/get_all_products.png)

#### 2. GET /products/\<id\> — Retrieve a product by ID

![GET /products/<id>](./img/get_product_by_id.png)

#### 3. POST /users — Register route (create a new user)

![POST /users](./img/register_user.png)

#### 4. GET /users/\<id\> — Retrieve route (user found & not found)

![GET /users/<id> — Found](./img/get_user_by_id.png)

![GET /users/<id> — Not Found](./img/get_user_by_id_not_found.png)

#### 5. Role column added to users without affecting existing rows

![role column in users table](./img/db_user_role_column.png)

#### 6. order_items association table exists

![order_items table](./img/db_order_items.png)

---

### Database Association & Verification

- **Association Table**: Defined in [`app/models/order.py`](./app/models/order.py) via `db.Table('order_items', ...)` with foreign keys `order_id` → `orders.id` and `product_id` → `products.id`, plus `quantity` and `price_at_purchase` columns.
- **Many-to-Many Query Verification**:
  ```sql
  SELECT * FROM order_items;
  ```
  _Output_:
  ```
   order_id | product_id | quantity | price_at_purchase
  ----------+------------+----------+-------------------
          1 |          1 |        1 |            199.99
          1 |          2 |        1 |            129.50
  ```
