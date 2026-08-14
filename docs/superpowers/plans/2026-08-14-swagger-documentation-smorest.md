# Swagger Documentation with Flask-Smorest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate flask-smorest to automatically document all user and product endpoints in Swagger UI at `/swagger-ui` and serve the schema at `/openapi.json`.

**Architecture:** We use marshmallow to define request and response schemas, subclass the flask-smorest `Api` to customize validation error formats for backward compatibility with existing tests, and decorate blueprint routes.

**Tech Stack:** Python 3.x, Flask, flask-smorest, marshmallow, apispec.

## Global Constraints
- Do not break existing API client response structures or test assertions.
- Intercept 422 validation errors to return 400 Bad Request matching existing error response formats.
- Retain all existing function docstrings and comments.

---

### Task 1: Scaffolding and Schema Definitions

**Files:**
- Modify: `requirements.txt`
- Create: `app/schemas.py`

**Interfaces:**
- Produces: Marshmallow validation/serialization schemas (`UserSchema`, `UserRegisterInputSchema`, `UserRegisterResponseSchema`, `UserLoginInputSchema`, `UserLoginResponseSchema`, `UserGetResponseSchema`, `ProductSchema`, `ProductListResponseSchema`, `ProductGetResponseSchema`).

- [ ] **Step 1: Update requirements.txt**
  Add `flask-smorest==0.47.0` and `marshmallow==4.3.1` to `requirements.txt`.
- [ ] **Step 2: Define marshmallow schemas in app/schemas.py**
  Write the schemas mirroring input payloads and response formats.
- [ ] **Step 3: Commit**
  ```bash
  git add requirements.txt app/schemas.py
  git commit -m "chore: add flask-smorest and marshmallow schema definitions"
  ```

---

### Task 2: Config and Extensions Setup

**Files:**
- Modify: `app/config.py`
- Modify: `app/extensions.py`
- Modify: `app/__init__.py`

**Interfaces:**
- Consumes: Config settings and marshmallow schemas.
- Produces: Customized `CustomApi` instance registering blueprints and serving Swagger UI.

- [ ] **Step 1: Update config.py with OpenAPI keys**
  Add `API_TITLE`, `API_VERSION`, `OPENAPI_VERSION`, `OPENAPI_URL_PREFIX`, `OPENAPI_SWAGGER_UI_PATH`, `OPENAPI_SWAGGER_UI_URL`.
- [ ] **Step 2: Subclass Api and define CustomApi in extensions.py**
  Override `handle_http_exception` to translate status code 422 to 400 with `success: False` responses for testing consistency.
- [ ] **Step 3: Initialize CustomApi in app/__init__.py**
  Import and initialize `api` on `flask_app` and register blueprints on `api`.
- [ ] **Step 4: Commit**
  ```bash
  git add app/config.py app/extensions.py app/__init__.py
  git commit -m "feat: initialize custom api and swagger configuration"
  ```

---

### Task 3: Migrate Blueprint and Decorate Product Routes

**Files:**
- Modify: `app/routes/products.py`

**Interfaces:**
- Consumes: `ProductSchema`, `ProductListResponseSchema`, `ProductGetResponseSchema`.

- [ ] **Step 1: Refactor products.py routes**
  Change import to `from flask_smorest import Blueprint`. Decorate `@products_bp.route('/products')` and `/products/<int:id>` with response decorators.
- [ ] **Step 2: Commit**
  ```bash
  git add app/routes/products.py
  git commit -m "feat: decorate product endpoints with flask-smorest schemas"
  ```

---

### Task 4: Migrate Blueprint and Decorate User Routes

**Files:**
- Modify: `app/routes/users.py`

**Interfaces:**
- Consumes: `UserRegisterInputSchema`, `UserRegisterResponseSchema`, `UserLoginInputSchema`, `UserLoginResponseSchema`, `UserGetResponseSchema`.

- [ ] **Step 1: Refactor users.py routes**
  Change import to `from flask_smorest import Blueprint`. Update view function parameters and bodies to read parsed data. Decorate routes with validation and response decorators.
- [ ] **Step 2: Commit**
  ```bash
  git add app/routes/users.py
  git commit -m "feat: decorate user endpoints with validation and response schemas"
  ```

---

### Task 5: Testing and Swagger Verification

**Files:**
- Create: `test/test_swagger.py`

**Interfaces:**
- Produces: Automated unit tests asserting `/swagger-ui` and `/openapi.json` load correctly.

- [ ] **Step 1: Write test/test_swagger.py**
  Add unit tests that assert OpenAPI schema correctness and HTML loading.
- [ ] **Step 2: Run test suite**
  Run: `./venv/bin/python -m unittest discover -s test`
  Expected: PASS
- [ ] **Step 3: Commit**
  ```bash
  git add test/test_swagger.py
  git commit -m "test: add unit tests for swagger ui and openapi json"
  ```
