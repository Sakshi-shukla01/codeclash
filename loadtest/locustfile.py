"""
Load test: bahut saare fake users ek saath API use karte hain. Resume ke numbers yahin se aate hain.

Install:  pip install locust
Chalao:   locust -f loadtest/locustfile.py --host http://localhost:8000
Phir browser mein http://localhost:8089 kholo -> users (jaise 100) aur spawn rate (10) daalo -> Start.

Dekho: requests/sec, p95 latency, failures. Screenshot lo, README mein daalo.
Judge throughput test karne ke liye:  docker compose up --scale judge=4  aur compare karo.
"""
import random
import uuid

from locust import HttpUser, between, task

SOLUTION = "a,b=map(int,input().split())\nprint(a+b)"


class Player(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        name = f"load_{uuid.uuid4().hex[:10]}"
        r = self.client.post("/api/v1/auth/signup",
                             json={"username": name, "email": f"{name}@load.test", "password": "secret123"})
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    @task(5)
    def browse_problems(self):
        self.client.get("/api/v1/problems")

    @task(3)
    def leaderboard(self):
        self.client.get("/api/v1/leaderboard")

    @task(2)
    def view_problem(self):
        slug = random.choice(["sum-of-two", "two-sum", "palindrome-check", "count-primes"])
        self.client.get(f"/api/v1/problems/{slug}", name="/api/v1/problems/[slug]")

    @task(1)
    def submit_practice(self):
        # 429 (cooldown) expected hai jab user bahut jaldi submit kare -> failure nahi maante
        with self.client.post("/api/v1/submissions", headers=self.headers,
                              json={"problem_slug": "sum-of-two", "code": SOLUTION},
                              catch_response=True) as r:
            if r.status_code in (202, 429):
                r.success()
