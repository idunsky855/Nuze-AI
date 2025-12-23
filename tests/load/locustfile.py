import logging
import random
import string
from locust import HttpUser, task, between

class NuzeUser(HttpUser):
    wait_time = between(1, 3)  # Wait between 1 and 3 seconds between tasks
    email = None
    password = "password123"
    token = None

    def on_start(self):
        """
        Executed when a simulated user starts.
        Registers a new unique user and logs them in to get a token.
        """
        self.email = self._generate_random_email()
        self._signup_and_login()

    def _generate_random_email(self):
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"loadtest_{random_str}@example.com"

    def _signup_and_login(self):
        # 1. Signup
        signup_payload = {
            "email": self.email,
            "password": self.password,
            "full_name": "Load Test User"
        }
        with self.client.post("/auth/signup", json=signup_payload, catch_response=True) as response:
            if response.status_code == 201:
                logging.info(f"Created user: {self.email}")
            elif response.status_code == 400 and "already exists" in response.text:
                # If user exists (unlikely with random email but possible), try logging in directly
                logging.info(f"User {self.email} already exists, proceeding to login.")
            else:
                logging.error(f"Failed to create user {self.email}: {response.text}")
                response.failure(f"Signup failed: {response.text}")
                return

        # 2. Login
        login_payload = {
            "username": self.email,  # OAuth2 form expects 'username'
            "password": self.password
        }
        with self.client.post("/auth/login", data=login_payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                logging.info(f"Logged in user: {self.email}")
            else:
                logging.error(f"Login failed for {self.email}: {response.text}")
                response.failure(f"Login failed: {response.text}")

    @task(1)
    def health_check(self):
        """
        Lightweight task: Check health endpoint.
        """
        self.client.get("/health", name="/health")

    @task(5)
    def get_feed(self):
        """
        Heavy task: Fetch personalized feed.
        Requires authentication.
        """
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test without skip/limit (default)
        self.client.get("/feed/", headers=headers, name="/feed/")

        # Occasional test with pagination
        if random.random() < 0.3:
            self.client.get("/feed/?skip=10&limit=10", headers=headers, name="/feed/ (paginated)")

    @task(3)
    def stress_auth(self):
        """
        Medium task: Hit login endpoint again to stress auth service.
        """
        login_payload = {
            "username": self.email,
            "password": self.password
        }
        self.client.post("/auth/login", data=login_payload, name="/auth/login (stress)")
