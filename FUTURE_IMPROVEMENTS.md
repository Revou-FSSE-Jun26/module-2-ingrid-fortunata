# RevoFashion API — Future Improvements & Technical Roadmap

This document outlines architectural, security, and feature improvements proposed for future development phases.

---

## 1. 🌐 Cross-Origin Resource Sharing (CORS) (Completed ✅)

### Overview
When frontend applications (e.g., React, Vue, Next.js) connect from a different domain or port (e.g., `http://localhost:5173` or `http://localhost:3000`), web browsers enforce Same-Origin Policy and issue preflight `OPTIONS` checks.

### Implementation
* Integrated `Flask-CORS` in [`app/extensions.py`](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/extensions.py) and [`app/__init__.py`](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/__init__.py).
* Configured `CORS_ALLOWED_ORIGINS` in [`app/config.py`](file:///Users/ingrid.fortunata/Desktop/Learning/Revou/module-2-ingrid-fortunata/app/config.py) allowing dynamic domain whitelist via `.env` (`CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173` or `*` for development) with `supports_credentials=True`.

---

## 2. 👤 User Profile & Password Management

### Endpoints

#### A. `PUT /users/<id>` (Update Profile) (Completed ✅)
* **Auth**: JWT Required
* **Permissions**:
  * **Customer**: Can update only their own profile (`username`, `email`).
  * **Superadmin**: Can update any profile, and additionally modify `role` (`superadmin`, `admin`, `customer`) or toggle `is_active` (ban/activate accounts). Non-superadmins attempting to modify `role` or `is_active` receive 403 Forbidden.
* **Validation**: Checks unique constraints for updated `username` and `email`, rejecting empty payload with 422.

#### B. `POST /auth/change-password`
* **Auth**: JWT Required (Current authenticated user)
* **Request Payload**:
  ```json
  {
    "old_password": "current_secret_password",
    "new_password": "new_secure_password"
  }
  ```
* **Logic**: Verifies `old_password` with `check_password_hash`, validates new password strength, and hashes new password before saving.

---

## 3. 👥 Superadmin User Management (`GET /users`) (Completed ✅)

### Overview
Superadmins have a centralized view of all registered customers and staff with filtering and pagination.

### Features
* **Auth**: JWT Required (`superadmin` only).
* **Endpoint**: `GET /users`
* **Query Filters**:
  * `?role=customer` | `admin` | `superadmin`
  * `?is_active=true` | `false`
  * `?search=alice` (searches across `username` and `email`)
  * `?page=1&per_page=10` (pagination)
* **Response**: Paginated list of user accounts (excluding `password_hash`).


---

## 4. 🩺 Database & API Health Check (`GET /health`)

### Overview
Production platforms (Render, Railway, Fly.io, AWS ECS, Kubernetes) require a healthcheck endpoint for readiness and liveness probes.

### Proposed Implementation
* **Endpoint**: `GET /health`
* **Logic**:
  ```python
  from sqlalchemy import text

  @flask_app.route('/health', methods=['GET'])
  def health_check():
      try:
          db.session.execute(text('SELECT 1'))
          db_status = "connected"
      except Exception as e:
          db_status = f"disconnected: {str(e)}"
          return {"status": "unhealthy", "database": db_status}, 503

      return {
          "status": "healthy",
          "database": db_status,
          "timestamp": datetime.now(timezone.utc).isoformat()
      }, 200
  ```

---

## 5. 📦 Product Partial Update (`PUT /products/<id>`)

### Overview
`PUT /products/<id>` supports flexible partial object payloads (`ProductUpdateInputSchema`). Clients can send only the fields they wish to modify (e.g. updating `stock` only, or updating `price` and `name`), without needing to resend the entire product body. Unprovided fields and images are preserved as-is.

### Usage Example (Update Stock Only)
* **Endpoint**: `PUT /products/<id>`
* **Auth**: JWT Required (`superadmin`, `admin`)
* **Request Payload**:
  ```json
  {
    "stock": 50
  }
  ```
* **Response**: Updated product detail with preserved existing attributes.

---

## 6. 🔒 Enhanced Password Strength Rules

### Overview
Currently, passwords require `min=6` characters.

### Proposed Implementation
* Enforce password complexity via regex in `UserRegisterInputSchema`:
  * Minimum 8 characters
  * At least 1 uppercase letter (`A-Z`)
  * At least 1 lowercase letter (`a-z`)
  * At least 1 number (`0-9`)
  * At least 1 special character (`!@#$%^&*`)

---

## 7. 🚚 Order Lifecycle Analytics & Stage Timestamps

### Current Implementation (Completed ✅)
* `tracking_number` (`VARCHAR(100)`): Required for admins/superadmins when transitioning order status to `shipped`.
* `cancellation_reason` (`TEXT`): Required for all roles when transitioning order status to `cancelled` (via `PATCH` or `DELETE`).
* Status updates automatically update `updated_at` on the `orders` record.

### Future Roadmap
* `paid_at`, `shipped_at`, `delivered_at`, `cancelled_at` (`TIMESTAMP`): Dedicated event timestamps for advanced fulfillment analytics and SLA reporting.

---

## 8. 📧 Asynchronous Notifications & Webhooks

### Overview
Offload slow I/O tasks to a background worker (e.g., Celery / Redis Queue).

### Proposed Workflows:
1. **Order Confirmation Email**: Send automated receipt upon `POST /orders`.
2. **Shipping Update Notification**: Send tracking details when order transitions to `shipped`.
3. **Payment Webhook**: Endpoint to receive payment confirmation from gateways (Midtrans, Xendit, Stripe) to automatically transition status from `pending` to `paid`.
