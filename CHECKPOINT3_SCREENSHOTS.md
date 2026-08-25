# 📷 RevoFashion API — Postman & Database Verification Screenshots

This document serves as the visual verification documentation for **Checkpoint 3 / Final Project Deliverables** of the RevoFashion API.

All screenshots demonstrate real API execution against live endpoints using **Postman**, verifying correct HTTP status codes, JSON payload responses, header authentication, error handling, and database updates.

---

## 📋 Summary of Verified Endpoints

| Category | HTTP Method | Endpoint | Description | Status Code | Screenshot |
| :--- | :---: | :--- | :--- | :---: | :---: |
| **Products** | `GET` | `/products` | Fetch paginated product catalog with filters | `200 OK` | [View](#1-get-products) |
| **Products** | `POST` | `/products` | Create product with base64 gallery images | `201 Created` | [View](#2-post-products) |
| **Products** | `PUT` | `/products/:id` | Update product details & inventory stock | `200 OK` | [View](#3-put-productsid) |
| **Products** | `DELETE` | `/products/:id` | Delete product (guarded by active orders) | `204 No Content` / `409` | [View](#4-delete-productsid) |
| **Categories** | `POST` | `/categories` | Create new clothing category | `201 Created` | [View](#5-post-categories) |
| **Categories** | `PUT` | `/categories/:id` | Update category name & description | `200 OK` | [View](#6-put-categoriesid) |
| **Categories** | `DELETE` | `/categories/:id` | Delete category (guarded by active items) | `204 No Content` / `409` | [View](#7-delete-categoriesid) |
| **Orders** | `POST` | `/orders` | Place authenticated order with size/color variants | `201 Created` | [View](#8-post-orders) |
| **Orders** | `GET` | `/orders/:id` | Retrieve order detail with price & item snapshots | `200 OK` | [View](#9-get-ordersid) |
| **Orders** | `PATCH` | `/orders/:id` | Update order state (pending ➔ paid ➔ processing) | `200 OK` | [View](#10-patch-ordersid) |
| **Orders** | `DELETE` | `/orders/:id` | Soft-cancel order & restore product stock | `200 OK` | [View](#11-delete-ordersid) |

---

## 🛍️ 1. Products Catalog API Verification

### 1. GET `/products`
- **Description**: Public product catalog retrieval supporting pagination, search, sorting, and fashion filters (`gender`, `size`, `color`, `material`).
- **Response Status**: `200 OK`

![GET All Products](./img/checkpoint3/postman_get_all_products.png)

---

### 2. POST `/products`
- **Description**: Admin endpoint to create a new product with fashion attributes (`size`, `color`, `material`, `gender`, `sku`) and up to 3 base64 image objects.
- **Response Status**: `201 Created`

![POST Create Product](./img/checkpoint3/postman_post_product.png)

---

### 3. PUT `/products/:id`
- **Description**: Admin endpoint to update product details, unit prices, stock balances, or image galleries (supports partial payload updates).
- **Response Status**: `200 OK`

![PUT Update Product](./img/checkpoint3/postman_update_product.png)

---

### 4. DELETE `/products/:id`
- **Description**: Admin endpoint to delete a product. If linked to active orders, deletion is blocked with `409 Conflict`. If linked only to finished orders, soft-deletes (`is_active = false`). If never ordered, hard-deletes (`204 No Content`).
- **Response Status**: `204 No Content` / `409 Conflict`

![DELETE Product](./img/checkpoint3/postman_delete_product.png)

---

## 🏷️ 2. Categories Management Verification

### 5. POST `/categories`
- **Description**: Admin endpoint to create a new category with unique name validation.
- **Response Status**: `201 Created`

![POST Category](./img/checkpoint3/postman_post_category.png)

---

### 6. PUT `/categories/:id`
- **Description**: Admin endpoint to update category fields (`name`, `description`, `is_active`) enforcing name uniqueness.
- **Response Status**: `200 OK`

![PUT Category](./img/checkpoint3/postman_put_category.png)

---

### 7. DELETE `/categories/:id`
- **Description**: Admin endpoint to delete a category. Blocked with `409 Conflict` if the category has active products linked to it.
- **Response Status**: `204 No Content` / `409 Conflict`

![DELETE Category](./img/checkpoint3/postman_delete_category.png)

---

## 🛒 3. Orders Lifecycle Verification

### 8. POST `/orders`
- **Description**: Customer endpoint to place an order. Validates stock availability, decrements inventory, records recipient shipping details, and snapshots unit price, size, and color.
- **Response Status**: `201 Created`

![POST Create Order](./img/checkpoint3/postman_post_order.png)

---

### 9. GET `/orders/:id`
- **Description**: Authenticated customer or admin endpoint to retrieve order details and purchased item snapshots.
- **Response Status**: `200 OK`

![GET Order by ID](./img/checkpoint3/postman_get_order.png)

---

### 10. PATCH `/orders/:id`
- **Description**: Admin or customer endpoint to progress order status following state machine rules (`pending` ➔ `paid` ➔ `processing` ➔ `shipped` ➔ `delivered`).
- **Response Status**: `200 OK`

![PATCH Order Status](./img/checkpoint3/postman_patch_order.png)

---

### 11. DELETE `/orders/:id`
- **Description**: Soft-cancel an in-progress order (`pending` or `paid`), recording a mandatory cancellation reason, restoring product stock balances, and returning `200 OK`.
- **Response Status**: `200 OK`

![DELETE Cancel Order](./img/checkpoint3/postman_delete_order.png)

---

## 🗄️ 4. PostgreSQL Production Database Verification

### PostgreSQL Table Views (pgAdmin / DBeaver)

![Database Order Items Table](./img/db_order_items.png)

*Figure: Production database view showing `order_items` junction table snapshotting `price_at_purchase`, `size`, `color`, and `quantity`.*
