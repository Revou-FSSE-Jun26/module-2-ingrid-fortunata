[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoShop API - Backend Development Project

This repository contains the backend code for **RevoShop**, a fictional e-commerce platform. It is being built progressively across bi-weekly checkpoints.

---

## Checkpoint 1: Database Design

This checkpoint focuses on setting up the initial PostgreSQL database schema and populating it with sample data.

### How to set up the database locally

1. **Install PostgreSQL** (if you haven't already). Ensure you have set a password for the `postgres` superuser.
2. **Create the database**:
   - Open **pgAdmin** or use `psql` in your terminal.
   - Create a new database named `revoshop_db`.
     ```sql
     CREATE DATABASE revoshop_db;
     ```
3. **Execute SQL scripts**:
   - Connect to the `revoshop_db` database.
   - Execute the `schema.sql` file first to create all the necessary tables.
   - Execute the `seed.sql` file to populate the tables with sample data.
   - (Optional) Run the queries inside `queries.sql` to verify the data.

### Database Schema Overview

The database consists of 5 tables:

- `users`: Stores user account records.
- `categories`: Product categories.
- `products`: Store items, linked to a category.
- `orders`: Orders placed by a user.
- `order_items`: A junction table linking `orders` and `products` (many-to-many relationship).

For detailed documentation on database design decisions and foreign key constraint rules (such as why `ON DELETE RESTRICT` is used), please refer to [SCHEMA_DOCUMENTATION.md](./SCHEMA_DOCUMENTATION.md).

#### Database Schema Diagram

![Database Schema Diagram](./img/diagram.png)

---

## Checkpoint 2: Flask & SQLAlchemy Layer

This checkpoint stands up the Flask application layer, connects it to PostgreSQL via SQLAlchemy, models all database tables and relationships (including the many-to-many relationship via `order_items`), implements Flask-Migrate schema history, and provides initial API endpoints.

### Project Architecture & Structure

```
module-2-ingrid-fortunata/
├── app/
│   ├── __init__.py           # Flask app factory, SQLAlchemy db & Migrate initialization
│   ├── config.py             # Config management & DATABASE_URL parsing
│   ├── extensions.py         # SQLAlchemy & Migrate extension instances
│   ├── models/
│   │   ├── __init__.py       # Model exports
│   │   ├── user.py           # User model with id, username, email, password_hash, role, created_at
│   │   ├── category.py       # Category model
│   │   ├── product.py        # Product model
│   │   └── order.py          # Order model & order_items association table (db.Table)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── products.py      # Hardcoded product endpoints (GET /products, GET /products/<id>)
│   │   └── users.py         # User endpoints (POST /users, GET /users/<id>)
│   └── seed_data.py          # Sample data populator for many-to-many relationship
├── migrations/               # Flask-Migrate / Alembic migration history
├── .env                      # Local environment configuration (ignored in git)
├── .env.example              # Template environment configuration
├── requirements.txt          # Project dependencies
├── run.py                    # Application entry point
└── test_checkpoint2.py       # Automated test suite for Checkpoint 2 endpoints
```

---

### How to Run & Verify Checkpoint 2 Locally

1. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and verify your local PostgreSQL connection string:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/revoshop_db
   SECRET_KEY=dev-secret-key-change-in-production
   ```

3. **Apply Database Migrations**:
   Run database migrations using Flask-Migrate:
   ```bash
   flask db upgrade
   ```
   *Note*: The migration history includes:
   - Initial migration: Base tables (`users`, `categories`, `products`, `orders`, `order_items`).
   - Revision `aa0fd34ebf0e`: Migration adding the `role` column to `User` model without affecting existing database rows.

4. **Seed Sample Many-to-Many Data**:
   ```bash
   PYTHONPATH=. python3 app/seed_data.py
   ```
   This inserts sample categories, products, a user (`alice_smith`), and an order linked to multiple products through the `order_items` association table.

5. **Run the Flask Development Server**:
   ```bash
   python3 run.py
   ```
   The application will start on `http://127.0.0.1:5000`.

6. **Run Automated Test Suite**:
   ```bash
   PYTHONPATH=. python3 test_checkpoint2.py
   ```

---

### Implemented Endpoints Matrix

| HTTP Method | Endpoint | Description | Status Code | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/products` | List all hardcoded products | `200 OK` | Warm-up endpoint returning JSON array using `jsonify()`. |
| `GET` | `/products/<id>` | Get specific product by ID | `200 OK` / `404` | Filters hardcoded list; returns `404 Not Found` if missing. |
| `POST` | `/users` | Register a new user | `201 Created` | Saves new `User` to PostgreSQL via `db.session.add()` & `db.session.commit()`. |
| `GET` | `/users/<id>` | Retrieve user by ID | `200 OK` / `404` | Queries database via `db.session.get()`; handles `404` if not found. |

---

### Database Association & Verification

- **Association Table**: Defined in [app/models/order.py](./app/models/order.py) via `db.Table('order_items', ...)` with foreign keys `order_id` -> `orders.id` and `product_id` -> `products.id`.
- **Many-to-Many Query Verification**:
  ```sql
  SELECT * FROM order_items;
  ```
  *Output*:
  ```
   order_id | product_id | quantity | price_at_purchase 
  ----------+------------+----------+-------------------
          1 |          1 |        1 |            199.99
          1 |          2 |        1 |            129.50
  ```
