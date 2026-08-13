# Design Specification: Active Flagging & User Login Endpoint

This document outlines the design for adding status flagging (`is_active`) to `User`, `Product`, and `Category` entities, and implementing a secure login endpoint (`/users/login`).

---

## 1. Database Model & Schema Changes

We will introduce a boolean flag `is_active` to denote the state of three core entities: Users, Products, and Categories.

### 1.1 SQLAlchemy Models (`app/models/`)

*   **User (`users` table)**:
    *   `is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)`
*   **Product (`products` table)**:
    *   `is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)`
*   **Category (`categories` table)**:
    *   `is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)`

All `to_dict()` methods will serialize `is_active`.

### 1.2 SQL Scripts (`queries/schema.sql`)

Update the table definitions in `queries/schema.sql` to match:
*   `users`: Add `is_active BOOLEAN DEFAULT TRUE NOT NULL`
*   `products`: Add `is_active BOOLEAN DEFAULT TRUE NOT NULL`
*   `categories`: Add `is_active BOOLEAN DEFAULT TRUE NOT NULL`

---

## 2. API Endpoint Logic

### 2.1 Products API (`app/routes/products.py`)

*   **Refactoring to Database**: Replace the hardcoded list `HARDCODED_PRODUCTS` with direct queries to the `Product` model.
*   **Active-Only Filter (`GET /products`)**:
    *   Only return products where `Product.is_active` is `True` and whose associated `Category.is_active` is `True` (or has no category).
*   **Product Details (`GET /products/<int:id>`)**:
    *   Query by ID. If product doesn't exist, is inactive, or belongs to an inactive category, return `404 Not Found`.

### 2.2 Users API (`app/routes/users.py`)

*   **Login Endpoint (`POST /users/login`)**:
    *   Accepts `username` or `email` and `password`.
    *   Validates input presence.
    *   Looks up the user in the database. If not found, return `401 Unauthorized` with an error message.
    *   Verifies the password:
        *   Checks using Werkzeug's `check_password_hash` if the stored hash starts with `pbkdf2:sha256:`.
        *   Falls back to plaintext equality check for development compatibility.
    *   Verifies user is active:
        *   If `user.is_active` is `False`, return `403 Forbidden` with `"Account is deactivated."`.
    *   Returns `200 OK` with user details on success.

---

## 3. Migration and Seed Updates

*   Generate a Flask-Migrate script to apply changes to the local PostgreSQL database.
*   Update database seeding `app/seed_data.py` and `queries/seed.sql` to include `is_active` flags.
