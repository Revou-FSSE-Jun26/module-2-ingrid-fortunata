[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoFashion API — Online Clothing Store Backend

## Executive Overview

**RevoFashion** is a fashion-focused e-commerce RESTful backend API inspired by **Uniqlo**, built using **Flask**, **SQLAlchemy ORM**, **Flask-Smorest (OpenAPI 3.0 / Swagger)**, and **PostgreSQL**. 

It handles user registration & authentication, clothing product catalog management with fashion attributes (`size`, `color`, `material`, `gender`, `sku`), category organization, search & filtering, order placement with variant tracking, stock auto-management, and order lifecycle state enforcement via Role-Based Access Control (RBAC) with simplified roles (`superadmin`, `admin`, `customer`).

This document serves as a complete technical guide for **Backend Developers** (understanding architecture, DB design rationale, ORM models, migrations, and local setup) and **Frontend Developers** (implementing UI workflows, request payloads, response formats, headers, and enum options).

---

## Local Setup & Backend Database Loading Guide

Follow these step-by-step instructions to set up the environment and seed PostgreSQL locally.

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 14+** running locally on port `5432`
- Terminal tool (`psql`) or graphical client (pgAdmin / DBeaver)

---

### Step-by-Step Setup

#### Step 1: Create PostgreSQL Database

Launch PostgreSQL CLI or pgAdmin and execute:

```sql
CREATE DATABASE revoshop_db;
```

---

#### Step 2: Clone Repository & Virtual Environment Setup

```bash
# Navigate to project workspace
cd module-2-ingrid-fortunata

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

#### Step 3: Configure Local Environment Variables

Copy `.env.example` to `.env` and fill in your local PostgreSQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/revoshop_db
```

> 💡 **Note**: Replace `postgres:postgres@localhost:5432` with your actual local PostgreSQL user, password, host, and port.

---

#### Step 4: Apply Database Migrations (Flask-Migrate / Alembic)

Run the migration command to construct all 6 PostgreSQL tables and indexes:

```bash
flask db upgrade
```

> **Migration History**:
> - Initial migration creates base tables: `users`, `categories`, `products`, `product_images`, `orders`, `order_items`.
> - Revision `aa0fd34ebf0e` applies the `role` column to `users`.
> - Revision `b102e24f5184` simplifies user roles, sets size default to 'Free Size', color to NOT NULL, gender default to 'Unisex', sku to NOT NULL with auto-generation, shipping fields to NOT NULL, and order items size/color to NOT NULL.

---

#### Step 5: Seed Sample Database Data

Populate your database with Uniqlo-inspired fashion categories, clothing products, pre-configured role users, and sample orders:

```bash
PYTHONPATH=. python3 app/seed_data.py
```

##### Pre-Configured Seed Users for Testing

| Username | Email | Password | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| `superadmin_user` | `superadmin@revofashion.com` | `superadmin_password` | `superadmin` | Full system access |
| `admin_user` | `admin@revofashion.com` | `admin_password` | `admin` | Catalog & order admin / staff |
| `alice_smith` | `alice@example.com` | `alice_password` | `customer` | Test customer |

---

#### Step 6: Start Development Server

```bash
python3 run.py
```

The API server will launch at: **`http://127.0.0.1:5000`**

---

#### Step 7: Access Interactive Swagger UI Documentation

Open your browser to test endpoints interactively:

> 🌐 **Swagger UI**: **`http://127.0.0.1:5000/swagger-ui`**  
> 📄 **OpenAPI Spec (JSON)**: **`http://127.0.0.1:5000/openapi.json`**

---

#### Step 8: (Optional) Run Automated Test Suite

```bash
PYTHONPATH=. python3 -m pytest test/
```

---

#### SQL Database Verification Queries

You can verify database seeding directly via `psql`:

```sql
-- Check created tables
\dt

-- Query order items junction table snapshotting
SELECT 
    o.id AS order_id, 
    u.username, 
    p.name AS product_name, 
    oi.size, 
    oi.color, 
    oi.quantity, 
    oi.price_at_purchase
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

---

## Core Features

- ✅ **PostgreSQL Schema (6 Tables)**: Normalized relational structure (`users`, `categories`, `products`, `product_images`, `orders`, `order_items`).
- ✅ **Fashion-Specific Attributes**: Dedicated support for clothing sizes (`XS`–`XXL`, `FREE`), colors, materials, target genders (`Men`, `Women`, `Unisex`, `Kids`), and unique SKUs.
- ✅ **Decoupled Product Gallery**: Product image gallery table supporting up to 3 base64-encoded images per product with primary image thumbnail selection.
- ✅ **Flexible Catalog Filtering & Search**: Filter `GET /products` by `gender`, `size`, `color`, `material`, free-text `search` (name & description), and pagination (`page`, `per_page`).
- ✅ **Historical Variant & Price Snapshotting**: `order_items` junction table snapshotting item price, size, and color at the exact moment of purchase so historical orders are immune to future catalog price changes or product updates.
- ✅ **Stateless JWT Authentication**: Secure authentication via `Flask-JWT-Extended` with 24-hour token expiration.
- ✅ **Role-Based Access Control (RBAC)**: Custom `@roles_required` decorator enforcing permission levels across 3 user roles (`superadmin`, `admin`, `customer`).
- ✅ **Order Lifecycle & State Machine**: Status transitions (`pending` → `paid` → `processing` → `shipped` → `delivered` or `cancelled`) with role enforcement.
- ✅ **Automated Stock Control**: Stock is decremented on order placement and restored upon order cancellation.
- ✅ **Soft-Cancel Order Deletion**: `DELETE /orders/<id>` performs a soft cancel (restores stock, sets status to `cancelled`, preserves audit row).
- ✅ **Consistent Error Responses**: All API errors — including schema validation failures (422), JWT issues, and server errors — return a unified `{error_code, message}` JSON shape via global error handlers.
- ✅ **OpenAPI 3.0 / Swagger UI**: Auto-generated interactive API docs via `Flask-Smorest` and `marshmallow`.

---

## Technology Stack & Architecture

| Layer / Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | 3.x | Primary programming language |
| **Flask** | 3.0.3 | Web framework & App Factory pattern |
| **Flask-SQLAlchemy** | 3.1.1 | Object-Relational Mapping (ORM) layer |
| **Flask-Migrate** | 4.0.7 | Database migration management (Alembic) |
| **Flask-Smorest** | 0.47.0 | OpenAPI 3.0 specification & Swagger UI generation |
| **Flask-JWT-Extended** | 4.6.0 | Stateless JSON Web Token authentication |
| **marshmallow** | 4.3.1 | Input validation & serialization schemas |
| **Werkzeug** | 3.1.8 | Secure password hashing (`generate_password_hash` / `check_password_hash`) |
| **psycopg2-binary** | 2.9.12 | PostgreSQL database driver |
| **python-dotenv** | 1.0.1 | Local environment configuration management |

### Project Directory Structure

```
module-2-ingrid-fortunata/
├── app/
│   ├── __init__.py           # Flask app factory; registers blueprints & extensions
│   ├── auth.py               # @roles_required() decorator for RBAC
│   ├── config.py             # Config class (DATABASE_URL, JWT, OpenAPI settings)
│   ├── extensions.py         # Extension instances (db, migrate, api, jwt)
│   ├── models/               # SQLAlchemy ORM Models
│   │   ├── __init__.py       # Model exports for migration discovery
│   │   ├── user.py           # User model
│   │   ├── category.py       # Category model
│   │   ├── product.py        # Product & ProductImage models
│   │   └── order.py          # Order model & order_items association table
│   ├── routes/               # Flask-Smorest API Blueprints
│   │   ├── users.py          # /auth/login, /users
│   │   ├── categories.py     # /categories
│   │   ├── products.py       # /products
│   │   └── orders.py         # /orders
│   ├── schemas/              # Marshmallow Validation & Serialization Schemas
│   │   ├── user.py           # User & Auth schemas
│   │   ├── category.py       # Category schemas
│   │   ├── product.py        # Product schemas
│   │   └── order.py          # Order & OrderItem schemas
│   └── seed_data.py          # Database seeding script (categories, products, users, orders)
├── migrations/               # Alembic database migration history
├── test/
│   └── test_new_endpoints.py # Automated test suite (pytest)
├── img/                      # ERD Diagram & media assets
├── queries/                  # SQL scripts for verification
├── .env.example              # Template for local environment variables
├── requirements.txt          # Python dependency specifications
└── run.py                    # Application entry point (`python3 run.py`)
```

---

## Database Schema Overview & Design Rationale (Why)

The database consists of **6 normalized tables** designed for scalable fashion e-commerce operations.

### Entity-Relationship Diagram (ERD)

![Database Schema Diagram](./img/diagram2.png)

---

### Detailed Table Specifications & Architectural Rationale

#### 1. `users` — User Account & RBAC Credentials

Stores registered user accounts, login credentials, and permission roles.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique user ID |
| `username` | `VARCHAR(50)` | `UNIQUE`, `NOT NULL` | Unique account username |
| `email` | `VARCHAR(120)` | `UNIQUE`, `NOT NULL` | Unique email address |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | PBKDF2/scrypt hashed password |
| `role` | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'customer'` | User role enum (`superadmin`, `admin`, `customer`) |
| `is_active` | `BOOLEAN` | `NOT NULL`, `DEFAULT true` | Account status toggle |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC` | Account creation timestamp |

- **Design Rationale (Why)**:
  - **Password Security**: Passwords are never stored in plain text. Hashing via Werkzeug ensures resistance to dictionary and rainbow table attacks.
  - **RBAC in User Record**: Storing `role` directly on the `users` table avoids join overhead when creating JWT claims and evaluating the `@roles_required` decorator on protected routes.
  - **Soft Disabling**: `is_active` allows disabling compromised or deactivated accounts without deleting historical orders linked to the user.

---

#### 2. `categories` — Product Categories

Organizes clothing items into logical catalog sections (e.g., *T-Shirts*, *Outerwear*).

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique category ID |
| `name` | `VARCHAR(100)` | `UNIQUE`, `NOT NULL` | Category name |
| `description` | `TEXT` | `NULLABLE` | Optional category overview |
| `is_active` | `BOOLEAN` | `NOT NULL`, `DEFAULT true` | Hides category from public list |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC` | Creation timestamp |

- **Design Rationale (Why)**:
  - **Catalog Normalization**: Separated from `products` to prevent text duplication and enable category-level filtering.
  - **Soft Catalog Hiding**: `is_active` lets admins temporarily hide an entire seasonal category from `GET /products` without deleting items.
  - **FK Protection (`ON DELETE SET NULL`)**: If a category is deleted, linked products have their `category_id` set to `NULL` (uncategorized) rather than deleting products.

---

#### 3. `products` — Apparel Catalog & Inventory

Stores clothing items with fashion-specific attributes and stock balances.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique product ID |
| `category_id` | `INTEGER` | `FK → categories.id (SET NULL)` | Linked category |
| `name` | `VARCHAR(150)` | `NOT NULL` | Clothing product title |
| `description` | `TEXT` | `NULLABLE` | Detailed description |
| `price` | `NUMERIC(10, 2)` | `NOT NULL` | Unit price |
| `stock` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Available stock count |
| `size` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'Free Size'` | Fashion size (`XS`, `S`, `M`, `L`, `XL`, `XXL`, `FREE`, `Free Size`) |
| `color` | `VARCHAR(50)` | `NOT NULL` | Color variation |
| `material` | `VARCHAR(150)` | `NULLABLE` | Fabric composition |
| `gender` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'Unisex'` | Target demographic (`Men`, `Women`, `Unisex`, `Kids`) |
| `sku` | `VARCHAR(50)` | `UNIQUE`, `NOT NULL` | Stock Keeping Unit code (auto-generated if omitted) |
| `is_active` | `BOOLEAN` | `NOT NULL`, `DEFAULT true` | Soft delete flag |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC` | Creation timestamp |
| `updated_at` | `TIMESTAMP` | `DEFAULT UTC` | Modification timestamp |

- **Design Rationale (Why)**:
  - **Financial Precision (`NUMERIC(10,2)`)**: Uses fixed-point decimals instead of `FLOAT` to eliminate binary floating-point rounding errors during price calculations.
  - **Fashion Attributes**: Built-in attributes (`size`, `color`, `material`, `gender`) reflect fashion retail standards (Uniqlo model).
  - **Unique SKU**: Enforces inventory uniqueness for warehouse stock tracking.
  - **Stock Guard**: `stock` is guarded at database and validation levels to prevent negative inventory during high-concurrency order placement.

---

#### 4. `product_images` — Product Image Gallery

Stores image records attached to products.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique image ID |
| `product_id` | `INTEGER` | `FK → products.id (CASCADE)`, `NOT NULL` | Parent product |
| `image_base64` | `TEXT` | `NOT NULL` | Base64-encoded image string (~1MB max) |
| `is_primary` | `BOOLEAN` | `NOT NULL`, `DEFAULT false` | Thumbnail selection flag |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC` | Upload timestamp |

- **Design Rationale (Why)**:
  - **Decoupled Gallery Table**: Normalizing images into a separate 1-to-many table allows products to store up to 3 images without cluttering the main `products` table.
  - **Cascade Cleanup (`CASCADE`)**: Deleting a product automatically cleans up its associated image records.
  - **Primary Image Flag (`is_primary`)**: Allows `GET /products` list view to instantly fetch thumbnail images via an optimized subquery without returning full image arrays.

---

#### 5. `orders` — Order Header & Lifecycle Management

Stores overall order metadata, buyer reference, status state, and delivery details.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique order ID |
| `user_id` | `INTEGER` | `FK → users.id (RESTRICT)`, `NOT NULL` | Customer who placed order |
| `total_amount` | `NUMERIC(10, 2)` | `NOT NULL`, `DEFAULT 0.00` | Order total monetary value |
| `status` | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'pending'` | Lifecycle status (`pending`, `paid`, `processing`, `shipped`, `delivered`, `cancelled`) |
| `shipping_address` | `TEXT` | `NOT NULL` | Delivery address snapshot |
| `recipient_name` | `VARCHAR(150)` | `NOT NULL` | Recipient full name snapshot |
| `recipient_phone` | `VARCHAR(30)` | `NOT NULL` | Contact phone number snapshot |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC` | Order timestamp |
| `updated_at` | `TIMESTAMP` | `DEFAULT UTC` | Last status update timestamp |

- **Design Rationale (Why)**:
  - **FK Restrict (`ON DELETE RESTRICT`)**: Prevents deleting a user account if that user has existing order records, guaranteeing audit integrity.
  - **Shipping Snapshot**: Stores `shipping_address`, `recipient_name`, and `recipient_phone` on the order header so subsequent profile address changes do not corrupt past delivery logs.
  - **Lifecycle Control**: `status` column acts as a formal state machine driving stock allocation and cancellation logic.

---

#### 6. `order_items` — Junction Table (Many-to-Many Association Table)

Associates `orders` and `products` while capturing transaction snapshots.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | `INTEGER` | `PK`, `FK → orders.id (RESTRICT)` | Linked order |
| `product_id` | `INTEGER` | `PK`, `FK → products.id (RESTRICT)` | Linked product |
| `quantity` | `INTEGER` | `NOT NULL`, `DEFAULT 1` | Purchased quantity |
| `price_at_purchase` | `NUMERIC(10, 2)` | `NOT NULL` | Snapshot unit price at purchase time |
| `size` | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'Free Size'` | Purchased size variant |
| `color` | `VARCHAR(50)` | `NOT NULL` | Purchased color variant |

- **Design Rationale (Why - CRITICAL)**:
  - **Price & Variant Snapshotting**: Stores `price_at_purchase`, `size`, and `color` directly in the junction table. **Why?** Product prices or available attributes in the catalog change over time. Snapshotting ensures past financial totals and customer order history remain 100% accurate and immutable regardless of catalog updates.
  - **FK Restrict (`RESTRICT`)**: Prevents hard-deleting catalog products that are referenced in order items, preserving historical purchase records.

---

## Role-Based Access Control (RBAC) & Role Options

User authorization is enforced via JWT claims and the custom `@roles_required` decorator located in `app/auth.py`.

### Available Role Options (`role`)

| Role | Access Scope & Description | Default? |
| :--- | :--- | :--- |
| `customer` | Standard retail customer. Can register, log in, place orders, view active products/categories, and view **only their own** profile and orders. | **Yes** (Default on `POST /users`) |
| `admin` | System administrator / Store staff. Full operational access over catalog, categories, user profiles, and order lifecycles/statuses. | No |
| `superadmin` | System owner. Unrestricted permissions across all system resources, users, configurations, and endpoints. | No |

---

## Order Lifecycle & Status Options State Machine

The `status` column on the `orders` table tracks the lifecycle of an order.

### Available Status Options (`status`)

| Status | Description |
| :--- | :--- |
| `pending` | Order placed, stock reserved, awaiting payment (Default on order creation) |
| `paid` | Customer completed payment |
| `processing` | Admin/staff is preparing items for dispatch |
| `shipped` | Order handed to logistics carrier |
| `delivered` | Order successfully delivered to recipient |
| `cancelled` | Order cancelled; stock automatically restored to inventory |

### Status Transition Flow & Permissions Matrix

Orders can only transition **forward** through the lifecycle or be **cancelled** from eligible early states (`pending` or `paid`).

```
pending ──→ paid ──→ processing ──→ shipped ──→ delivered
   │           │
   └───────────┴──────────────────────────────→ cancelled
```

| From Status \ To Status | `paid` | `processing` | `shipped` | `delivered` | `cancelled` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`pending`** | ✅ *(Customer/Admin)* | ❌ | ❌ | ❌ | ✅ *(Customer/Admin)* |
| **`paid`** | ❌ | ✅ *(Admin)* | ❌ | ❌ | ✅ *(Customer/Admin)* |
| **`processing`** | ❌ | ❌ | ✅ *(Admin)* | ❌ | ❌ |
| **`shipped`** | ❌ | ❌ | ❌ | ✅ *(Admin)* | ❌ |
| **`delivered`** | — | — | — | — | — *(Terminal state)* |
| **`cancelled`** | — | — | — | — | — *(Terminal state)* |

#### Stock Side-Effects & Soft-Cancel Rules

1. **Order Creation (`POST /orders`)**: Decrements `product.stock` by item `quantity` inside an atomic transaction. If stock is insufficient, request returns `400 Bad Request`.
2. **Order Cancellation (`PATCH /orders/<id>` with `status: cancelled` OR `DELETE /orders/<id>`)**: Automatically restores stock (`product.stock += item.quantity`) for all items in the order.
3. **Soft-Cancel Policy (`DELETE /orders/<id>`)**: Performing a `DELETE` request does **NOT** hard-delete the database row. It sets `status = 'cancelled'`, restores product stock, preserves historical financial audit records, and returns the cancelled order object.
4. **Delivered Protection**: Orders in `delivered` status cannot be cancelled or refunded.

---

## API Reference Guide

### General API Conventions

- **Base URL**: `http://127.0.0.1:5000`
- **Request/Response Format**: `application/json`
- **Authentication Header**:
  ```http
  Authorization: Bearer <your_jwt_token>
  ```
- **Standard Error Response Structure**:
  ```json
  {
    "error_code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID 999 not found."
  }
  ```
- **Standard Validation Error Structure (422 Unprocessable Entity)**:
  All schema validation failures return a consistent structured response:
  ```json
  {
    "error_code": "VALIDATION_ERROR",
    "message": "Request body failed validation.",
    "details": {
      "json": {
        "price": ["Price must be greater than zero."],
        "color": ["Field cannot be blank or whitespace only."]
      }
    }
  }
  ```

---

### 📝 RESTful `PUT` Convention: Full Object Replacement

Following standard REST architectural principles, the **`PUT`** HTTP method represents a **full object replacement** of the target resource. When issuing a `PUT` request, clients must supply the complete entity state.

#### Example: `PUT /products/<id>` (Full Body Payload)
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
      "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "is_primary": true
    }
  ]
}
```

---

### Endpoint Reference Summary

#### 1. Authentication & User Management

##### `POST /auth/login`
- **Auth**: None
- **Description**: Authenticate user credentials and receive a JWT Bearer token.
- **Request Body Payload**:
  | Field | Type | Required | Validation / Options |
  | :--- | :--- | :---: | :--- |
  | `username` | String | Optional* | Account username (*Must provide either `username` or `email`) |
  | `email` | String | Optional* | Valid email format |
  | `password` | String | **Required** | Plain-text account password, non-blank |
- **Success Response (`200 OK`)**:
  ```json
  {
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user": {
        "id": 1,
        "username": "alice_smith",
        "email": "alice@example.com",
        "role": "customer",
        "is_active": true,
        "created_at": "2026-08-19T10:00:00+00:00"
      }
    }
  }
  ```
- **Error Responses**:
  | Status | `error_code` | Reason |
  | :--- | :--- | :--- |
  | `401 Unauthorized` | `USER_UNAUTHORIZED` | Wrong credentials, user not found, or account deactivated |
  | `422 Unprocessable Entity` | `VALIDATION_ERROR` | Missing required fields (e.g., no password, no username/email) |

  > ⚠️ **Security note**: Deactivated accounts return `401` (same as wrong credentials) — not `403` — to prevent leaking account state to unauthorized callers.

---

##### `POST /users`
- **Auth**: None
- **Description**: Register a new user account. All public registrations default to the `customer` role. Role assignment is a privileged admin operation and cannot be set through this endpoint.
- **Request Body Payload**:
  | Field | Type | Required | Options / Validation |
  | :--- | :--- | :---: | :--- |
  | `username` | String | **Required** | Unique, no spaces, non-blank |
  | `email` | String | **Required** | Valid email format, unique |
  | `password` | String | **Required** | Minimum 6 characters, non-blank |
- **Success Response (`201 Created`)**: Returns created user profile.
- **Error Responses**:
  | Status | `error_code` | Reason |
  | :--- | :--- | :--- |
  | `409 Conflict` | `USER_NAME_CONFLICT` | Username already registered |
  | `409 Conflict` | `USER_EMAIL_CONFLICT` | Email already registered |
  | `422 Unprocessable Entity` | `VALIDATION_ERROR` | Field validation failed (e.g., blank password) |

---

##### `GET /users/<id>`
- **Auth**: JWT Required (`Authorization: Bearer <token>`)
- **Permissions**: Customers can access **only their own** profile (`user_id == id`). Admins and superadmins can view any profile.
- **Success Response (`200 OK`)**: Returns user profile details.

---

#### 2. Products Catalog

##### `GET /products`
- **Auth**: None
- **Description**: Retrieve active clothing products with pagination and fashion attribute filters.
- **Query Parameters**:
  | Parameter | Type | Options / Enums | Description |
  | :--- | :--- | :--- | :--- |
  | `gender` | String | `Men`, `Women`, `Unisex`, `Kids` | Filter by target demographic |
  | `size` | String | `XS`, `S`, `M`, `L`, `XL`, `XXL`, `FREE` | Filter by clothing size |
  | `color` | String | Case-insensitive substring | Filter by color (e.g., `Navy`, `White`) |
  | `material` | String | Case-insensitive substring | Filter by fabric (e.g., `Cotton`) |
  | `search` | String | Free-text string | Search across product `name` and `description` |
  | `page` | Integer | Min `1` | Page number for pagination |
  | `per_page` | Integer | Min `1`, Max `100` (Default: `10`) | Items per page |
- **Success Response (`200 OK`)**:
  ```json
  {
    "data": [
      {
        "id": 1,
        "category_id": 1,
        "name": "AIRism Cotton Crew Neck T-Shirt",
        "description": "Smooth AIRism cotton blend...",
        "price": 14.9,
        "stock": 200,
        "size": "M",
        "color": "White",
        "material": "58% Cotton, 38% Polyester, 4% Spandex",
        "gender": "Men",
        "sku": "RF-TS-001",
        "primary_image": "data:image/jpeg;base64,...",
        "is_active": true,
        "created_at": "2026-08-19T10:00:00+00:00",
        "updated_at": "2026-08-19T10:00:00+00:00"
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 15,
    "pages": 2
  }
  ```

---

##### `GET /products/<id>`
- **Auth**: None
- **Description**: Retrieve a single active product with its complete image gallery.
- **Success Response (`200 OK`)**: Includes `images` array containing base64 images and `is_primary` flags.

---

##### `POST /products`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Description**: Create a new clothing product.
- **Request Body Payload**:
  | Field | Type | Required | Options / Enums / Validation |
  | :--- | :--- | :---: | :--- |
  | `name` | String | **Required** | Product title |
  | `price` | Float | **Required** | Must be `> 0` |
  | `stock` | Integer | **Required** | Must be `>= 0` |
  | `color` | String | **Required** | Color name |
  | `category_id` | Integer | Optional | Valid category ID |
  | `size` | String | Optional | Options: `XS`, `S`, `M`, `L`, `XL`, `XXL`, `FREE`, `Free Size` (Default: `Free Size`) |
  | `material` | String | Optional | Fabric composition |
  | `gender` | String | Optional | Options: `Men`, `Women`, `Unisex`, `Kids` (Default: `Unisex`) |
  | `sku` | String | Optional | Unique SKU code (auto-generated if omitted) |
  | `images` | Array | Optional | Max 3 images. Object fields: `image_base64` (Max 1MB), `is_primary` (Boolean, max 1 primary) |

---

##### `PUT /products/<id>`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Description**: Full replacement update of a product entity and its image gallery.

---

##### `DELETE /products/<id>`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Description**: Delete a product based on order status policy:
  | Product Order History | Action Taken | Response Code | Description |
  | :--- | :--- | :---: | :--- |
  | **Has Active Orders** (`pending`, `paid`, `processing`, `shipped`) | **Blocked** | `409 Conflict` | Cannot delete product while orders are in progress. |
  | **Has Only Finished Orders** (`delivered`, `cancelled`) | **Soft-Delete** | `204 No Content` | Marks `is_active = false`, retiring it from the public catalog while preserving historical purchase records & DB foreign keys. |
  | **Never Ordered** | **Hard-Delete** | `204 No Content` | Completely removes product and images from database. |

---

#### 3. Categories Management

##### `GET /categories`
- **Auth**: None
- **Description**: Retrieve all active categories.

##### `GET /categories/<id>`
- **Auth**: None
- **Description**: Retrieve a category by ID along with its associated active products.

##### `POST /categories`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Request Payload**: `{"name": "Outerwear", "description": "Jackets & Coats", "is_active": true}`
- **Validation**: `name` must be non-blank and unique. Returns `409 Conflict` if name already exists.

##### `PUT /categories/<id>`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Validation**: `name` must be non-blank. Returns `409 Conflict` if new name already exists. Empty body (`{}`) returns `422`.

##### `DELETE /categories/<id>`
- **Auth**: JWT Required (`superadmin`, `admin`)
- **Description**: Delete a category. **Blocked with `409 Conflict`** if the category has active products linked to it. Reassign or deactivate those products first.

---

#### 4. Orders Lifecycle

##### `GET /orders`
- **Auth**: JWT Required
- **Permissions**: Customers receive **only their own** orders. Admins/superadmins view all system orders.

---

##### `GET /orders/<id>`
- **Auth**: JWT Required
- **Permissions**: Customers restricted to viewing their own orders. Returns full order detail including items snapshot array (`items`: `product_id`, `name`, `quantity`, `price_at_purchase`, `size`, `color`).

---

##### `POST /orders`
- **Auth**: JWT Required (All authenticated users)
- **Description**: Place a new order. Validates stock, decrements inventory, and records size/color variants (synced from product if not specified) and price snapshot. Shipping details are strictly required.
- **Request Body Payload**:
  ```json
  {
    "shipping_address": "Jl. Jendral Sudirman No. 45, Jakarta",
    "recipient_name": "Alice Smith",
    "recipient_phone": "+6281234567890",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "size": "M",
        "color": "White"
      }
    ]
  }
  ```
- **Field Validation**:
  | Field | Validation |
  | :--- | :--- |
  | `items` | Required, non-empty list. Duplicate `product_id`s within the same order are rejected (`422`). Distinct products (e.g. Size M + Size L) are accepted. |
  | `shipping_address` | Required, min 5 chars, non-blank |
  | `recipient_name` | Required, non-blank |
  | `recipient_phone` | Required, digits/spaces/dashes/parens, 7–20 chars (e.g. `+62 812-3456-7890`) |
  | `items[].product_id` | Required, must be `>= 1` |
  | `items[].quantity` | Required, must be `>= 1` |
  | `items[].size` | Optional — must be one of the valid sizes if provided |
  | `items[].color` | Optional — non-blank if provided |
- **Success Response (`201 Created`)**: Returns created order object.

---

##### `PATCH /orders/<id>`
- **Auth**: JWT Required
- **Description**: Update order lifecycle status following state machine rules. Restores stock if status transitions to `cancelled`.
- **Request Body Payload**:
  | Field | Type | Required | Options / Enums |
  | :--- | :--- | :---: | :--- |
  | `status` | String | **Required** | Options: `pending`, `paid`, `processing`, `shipped`, `delivered`, `cancelled` |

---

##### `DELETE /orders/<id>`
- **Auth**: JWT Required
- **Description**: Soft-cancel an order. Sets `status = 'cancelled'`, restores product stock balances to inventory, preserves order record for audit history, and returns `200 OK`.



---

## Frontend Integration Guidelines

### 1. Authentication Flow & Headers
1. Authenticate user via `POST /auth/login`.
2. Extract `token` from `response.data.data.token`.
3. Store token securely (e.g., HTTP-only cookie or memory).
4. Attach token to all protected API requests:
   ```javascript
   headers: {
     'Authorization': `Bearer ${token}`,
     'Content-Type': 'application/json'
   }
   ```

### 2. Rendering UI Select Controls (Enums)
- **Clothing Sizes**: Populate dropdowns with `["XS", "S", "M", "L", "XL", "XXL", "FREE", "Free Size"]`.
- **Gender Filter**: Populate tab filters with `["Men", "Women", "Unisex", "Kids"]`.
- **Order Status Badges**: Map status strings to UI badge colors:
  - `pending` ➔ Yellow / Orange
  - `paid` ➔ Light Blue
  - `processing` ➔ Blue
  - `shipped` ➔ Purple
  - `delivered` ➔ Green
  - `cancelled` ➔ Red / Gray

### 3. Product Base64 Image Handling
- Primary images on catalog list (`GET /products`) are returned in `primary_image`.
- Render base64 images directly in `<img>` tags:
  ```html
  <img src="data:image/jpeg;base64,..." alt="Product Image" />
  ```

---

## Backend Extension & Maintenance Guidelines

### Adding a New API Endpoint

1. **Define Schema**: Add input/output marshmallow schemas in `app/schemas/`.
2. **Create Controller**: Add route handler in `app/routes/` using Flask-Smorest blueprints:
   ```python
   @bp.route('/your-endpoint', methods=['POST'])
   @jwt_required()
   @roles_required('admin', 'superadmin')
   @bp.arguments(YourInputSchema)
   @bp.response(201, YourOutputSchema)
   def handle_endpoint(data):
       # Business logic here
       pass
   ```
3. **Database Migrations**: When modifying ORM models in `app/models/`:
   ```bash
   flask db migrate -m "Describe model changes"
   flask db upgrade
   ```
