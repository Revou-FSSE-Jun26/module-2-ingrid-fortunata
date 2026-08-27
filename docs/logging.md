# Logging Architecture & Observability Guide

## Overview

**RevoFashion** implements a robust, production-ready logging strategy using Python's standard `logging` library and `TimedRotatingFileHandler`. Logging is initialized globally during the Flask App Factory lifecycle in [`app/__init__.py`](../app/__init__.py).

```
                      ┌────────────────────────────────────────┐
                      │        Flask App Factory Lifecycle     │
                      │         (app.setup_logging())          │
                      └──────────────────┬─────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      ┌────────────────────────┐                  ┌────────────────────────┐
      │  StreamHandler         │                  │ TimedRotatingFileHandler│
      │  (Console / stdout)    │                  │ (logs/app.log)         │
      └────────────┬───────────┘                  └────────────┬───────────┘
                   │                                           │
                   ▼                                           ▼
      Real-Time Dev Terminal                      Daily Midnight Rotation
      & Docker / Cloud Logs                       (7-Day Retention Window)
```

---

## 1. Dual Logging Handlers

The application configures two distinct output channels:

1. **Console Stream Handler (`logging.StreamHandler`)**:
   - Streams formatted log records in real time to standard output (`stdout`).
   - Ideal for local terminal development, real-time debugging, and container runtime collectors (Docker, Railway, Render, AWS CloudWatch, Datadog).
2. **Rotating File Handler (`logging.handlers.TimedRotatingFileHandler`)**:
   - Persists all log records to [`logs/app.log`](../logs/app.log).
   - **Rotation Interval**: Automatically rotates at midnight every day (`when='midnight'`, `interval=1`).
   - **Retention Policy**: Retains the last 7 daily backup log archives (`backupCount=7`), automatically purging older log files to conserve disk space.
   - **Rotation Suffix**: Archived daily logs follow the naming convention `logs/app.log.YYYY-MM-DD`.

---

## 2. Standardized Log Format & Configuration

All log lines follow a consistent, easily parseable format defined in [`app/config.py`](../app/config.py):

```python
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
```

### Log Record Fields:
- **`asctime`**: Timestamp formatted as `YYYY-MM-DD HH:MM:SS`.
- **`levelname`**: Fixed 8-character width log severity (`DEBUG   `, `INFO    `, `WARNING `, `ERROR   `, `CRITICAL`).
- **`name`**: Python module namespace (e.g., `app`, `app.routes.users`, `app.routes.orders`).
- **`message`**: Clear, actionable operational message with contextual identifiers (`user_id`, `product_id`, `order_id`).

---

## 3. Environment-Aware Log Level Matrix

The root log level dynamically adjusts based on the runtime environment (or via explicit `LOG_LEVEL` environment variable override in `.env`):

| Environment (`FLASK_ENV`) | Default Log Level | Purpose / Output Behavior |
| :--- | :--- | :--- |
| **`local`** | `DEBUG` | Full verbosity; records fine-grained application events, DB transactions, and query details. |
| **`development`** | `INFO` | Standard operations; captures authentication attempts, lifecycle state transitions, and validation notices. |
| **`production`** | `WARNING` | High signal; only logs warnings, business rule violations, failed authorizations, and unexpected errors. |

### Overriding via `.env`:
```env
# Force DEBUG logging in any environment:
LOG_LEVEL=DEBUG
```

---

## 4. Key Logging Checkpoints Across the Application

- 🔑 **Authentication & User Management** (`app.routes.users`):
  - Login attempts with identity (username or email).
  - Successful logins with `user_id` and assigned role.
  - Failed logins distinguishing between bad credentials vs non-existent/deactivated accounts.
- 📦 **Products & Catalog** (`app.routes.products`, `app.routes.categories`):
  - Product creation, attribute modifications, and base64 image uploads.
  - Category additions, updates, and soft-deletions.
- 🛒 **Order Processing & Inventory** (`app.routes.orders`):
  - Order placement attempts with recipient contact and item counts.
  - Row-level stock locking (`with_for_update`) and inventory decrements.
  - Order status transitions (`pending` → `paid` → `processing` → `shipped` → `delivered`).
  - Soft-cancellations and automated inventory restorations.
- ⚠️ **Validation & Error Handling** (`app.errors`, `app.__init__`):
  - Schema validation failures (422) with field-specific issue descriptions.
  - 401 Unauthorized / 403 Forbidden access violations.
  - Unhandled 500 exceptions with stack trace preservation.

---

## 5. Sample Log Output Snippet

```text
2026-08-27 20:20:26 | INFO     | app | Initializing RevoFashion Flask application
2026-08-27 20:20:27 | INFO     | app.routes.users | POST /auth/login — login attempt for identity 'alice_smith'
2026-08-27 20:20:27 | INFO     | app.routes.users | Login successful for user_id=3 ('alice_smith')
2026-08-27 20:20:28 | WARNING  | app.routes.users | Login failed — incorrect password for 'alice_smith'
2026-08-27 20:20:28 | WARNING  | app | Validation error on POST /auth/login: {'json': {'identity': ["Either 'username' or 'email' must be provided."]}}
2026-08-27 20:20:28 | INFO     | app.routes.orders | POST /orders — user_id=3 placed order with 2 item(s)
2026-08-27 20:20:28 | INFO     | app.routes.orders | Stock updated for product_id=1: new_stock=48
2026-08-27 20:20:29 | INFO     | app.routes.orders | PATCH /orders/1 — status transitioned: 'pending' -> 'paid'
```
