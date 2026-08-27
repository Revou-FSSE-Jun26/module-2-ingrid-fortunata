"""
RevoFashion API Load & Performance Testing Suite using Locust.

Simulates realistic sequential customer journeys:
1. GET /products          -> Browse product catalog
2. GET /products/:id      -> View specific product details
3. POST /orders           -> Place an order with selected product variant
4. GET /orders/:id        -> Retrieve and verify the placed order
"""

import os
import random
import string
from dotenv import load_dotenv
from locust import HttpUser, SequentialTaskSet, task, between, events
from locust.shape import LoadTestShape

# Load local environment variables from .env
load_dotenv()


class CustomerJourneyTaskSet(SequentialTaskSet):
    """
    Simulates a strict sequential customer purchase journey:
    Step 1: GET all products (catalog browsing)
    Step 2: GET single product by ID (product detail view)
    Step 3: POST new order (checkout & purchase)
    Step 4: GET created order by ID (order tracking / receipt verification)
    """

    def on_start(self):
        """Initialize user-specific state for this iteration."""
        self.selected_product_id = None
        self.selected_product_size = "M"
        self.selected_product_color = "White"
        self.created_order_id = None

    @task
    def get_all_products(self):
        """Step 1: Fetch all active products and select one for purchasing."""
        with self.client.get(
            "/products",
            params={"page": 1, "per_page": 20},
            name="GET /products",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    payload = response.json()
                    products = payload.get("data", [])
                    if products:
                        # Randomly pick one product to distribute load across inventory
                        chosen = random.choice(products)
                        self.selected_product_id = chosen.get("id")
                        self.selected_product_size = chosen.get("size") or "M"
                        self.selected_product_color = chosen.get("color") or "White"
                        response.success()
                    else:
                        response.failure("Product catalog returned empty list")
                except Exception as exc:
                    response.failure(f"Failed to parse product response: {exc}")
            else:
                response.failure(f"GET /products failed with status {response.status_code}: {response.text}")

    @task
    def get_single_product(self):
        """Step 2: Fetch detailed metadata of the selected product."""
        if not self.selected_product_id:
            # Fallback to ID 1 if catalog was empty
            self.selected_product_id = 1

        with self.client.get(
            f"/products/{self.selected_product_id}",
            name="GET /products/[id]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Product might be inactive or not seeded
                response.failure(f"Product {self.selected_product_id} not found (404)")
            else:
                response.failure(f"GET /products/{self.selected_product_id} failed with status {response.status_code}")

    @task
    def post_new_order(self):
        """Step 3: Place a new order with the authenticated customer token."""
        if not self.selected_product_id:
            self.selected_product_id = 1

        order_payload = {
            "recipient_name": f"Locust Buyer {''.join(random.choices(string.ascii_uppercase, k=4))}",
            "recipient_phone": f"0812{random.randint(10000000, 99999999)}",
            "shipping_address": f"Jl. Performance Load Test No. {random.randint(1, 500)}, Jakarta",
            "items": [
                {
                    "product_id": self.selected_product_id,
                    "quantity": 1,
                    "size": self.selected_product_size,
                    "color": self.selected_product_color
                }
            ]
        }

        with self.client.post(
            "/orders",
            json=order_payload,
            headers=self.user.auth_headers,
            name="POST /orders",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                try:
                    data = response.json().get("data", {})
                    self.created_order_id = data.get("id")
                    response.success()
                except Exception as exc:
                    response.failure(f"Failed to parse order creation response: {exc}")
            elif response.status_code == 400:
                # Stock depletion or business validation error during high concurrency
                error_body = response.text
                if "INSUFFICIENT_STOCK" in error_body or "stock" in error_body.lower():
                    # Cleanly record expected stock exhaustion under high load
                    response.success()
                else:
                    response.failure(f"POST /orders validation error (400): {error_body}")
            else:
                response.failure(f"POST /orders failed with status {response.status_code}: {response.text}")

    @task
    def get_created_order(self):
        """Step 4: Retrieve the created order by ID to confirm order state."""
        if not self.created_order_id:
            # If order creation was skipped due to stock or failure, skip verification gracefully
            return

        with self.client.get(
            f"/orders/{self.created_order_id}",
            headers=self.user.auth_headers,
            name="GET /orders/[id]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure(f"Created order {self.created_order_id} could not be retrieved (404)")
            else:
                response.failure(f"GET /orders/{self.created_order_id} failed with status {response.status_code}")


class CustomerUser(HttpUser):
    """
    Locust Virtual Customer.
    Executes the sequential journey with realistic think times between tasks.
    Authenticates at startup via /auth/login to obtain JWT bearer token.
    """

    host = os.getenv("LOCUST_HOST", "http://127.0.0.1:5000")
    tasks = [CustomerJourneyTaskSet]
    wait_time = between(1.0, 2.5)  # 1 to 2.5 seconds pause between sequential actions

    def on_start(self):
        """Authenticate user upon spawning."""
        self.auth_headers = {}
        self.login_or_register()

    def login_or_register(self):
        """
        Authentication strategy:
        1. If LOCUST_USER_USERNAME & LOCUST_USER_PASSWORD are set in .env:
           Logs in with that single shared account.
        2. If omitted/commented out in .env:
           Dynamically registers a brand new unique user per virtual user (e.g. 50 distinct accounts for 50 users)
           and authenticates immediately.
        """
        username = os.getenv("LOCUST_USER_USERNAME")
        password = os.getenv("LOCUST_USER_PASSWORD")

        # 1. Attempt Single-User Login if credentials are provided in .env
        if username and password:
            login_res = self.client.post(
                "/auth/login",
                json={"username": username, "password": password},
                name="POST /auth/login"
            )

            if login_res.status_code == 200:
                token = login_res.json().get("data", {}).get("token")
                if token:
                    self.auth_headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    return

        # 2. Dynamic Unique Registration: creates a unique customer for every virtual user
        rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        new_username = f"locust_user_{rand_suffix}"
        new_email = f"{new_username}@locustloadtest.local"
        new_pass = "SecurePass123!"

        reg_res = self.client.post(
            "/users",
            json={"username": new_username, "email": new_email, "password": new_pass},
            name="POST /users (Dynamic Registration)"
        )

        if reg_res.status_code == 201:
            login_again = self.client.post(
                "/auth/login",
                json={"username": new_username, "password": new_pass},
                name="POST /auth/login"
            )
            if login_again.status_code == 200:
                token = login_again.json().get("data", {}).get("token")
                self.auth_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }


class GradualRampLoadShape(LoadTestShape):
    """
    Custom Load Shape for gradual ramp-up from 50 to 200 users:
    - Stage 1 (0 to 30s):   Ramp to 50 users (spawn_rate=10)
    - Stage 2 (30 to 90s):  Hold 50 users
    - Stage 3 (90 to 120s): Ramp to 100 users (spawn_rate=10)
    - Stage 4 (120 to 180s): Hold 100 users
    - Stage 5 (180 to 220s): Ramp to 200 users (spawn_rate=10)
    - Stage 6 (220 to 300s): Hold 200 users peak load

    Toggleable via LOCUST_USE_LOAD_SHAPE in .env:
    - If LOCUST_USE_LOAD_SHAPE=true: Predefined stages will run automatically.
    - If LOCUST_USE_LOAD_SHAPE=false (default): Locust Web UI allows custom users/spawn rate.
    """

    # If not explicitly enabled, mark as abstract so Locust Web UI allows manual user input
    abstract = os.getenv("LOCUST_USE_LOAD_SHAPE", "false").lower() not in ("true", "1", "yes")

    stages = [
        {"duration": 30, "users": 50, "spawn_rate": 10},
        {"duration": 90, "users": 50, "spawn_rate": 10},
        {"duration": 120, "users": 100, "spawn_rate": 10},
        {"duration": 180, "users": 100, "spawn_rate": 10},
        {"duration": 220, "users": 200, "spawn_rate": 10},
        {"duration": 300, "users": 200, "spawn_rate": 10},
    ]

    def tick(self):
        """Calculates current user count and spawn rate based on elapsed time."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None
