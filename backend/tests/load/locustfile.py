"""
Locust load testing for Ghostwriter API.

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Or headless:
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""
from locust import HttpUser, task, between, events
import random
import json


# Sample texts for analysis
SAMPLE_TEXTS = [
    """
    Artificial intelligence is transforming the world as we know it.
    Machine learning algorithms are becoming increasingly sophisticated.
    The future of technology looks incredibly promising.
    """,
    """
    The sun was setting over the mountains, casting long shadows across the valley.
    Sarah watched from her window, thinking about the day's events.
    It had been a difficult journey, but she felt at peace.
    """,
    """
    In this paper, we present a novel approach to natural language processing.
    Our method achieves state-of-the-art results on several benchmark datasets.
    The implications for the field are significant and far-reaching.
    """,
    """
    The quarterly report shows strong growth in all major segments.
    Revenue increased by 15% compared to the same period last year.
    We expect continued momentum in the coming quarters.
    """,
]


class GhostwriterUser(HttpUser):
    """Simulates a typical user of the Ghostwriter application."""
    
    wait_time = between(1, 5)
    token = None
    user_email = None
    
    def on_start(self):
        """Called when a user starts - handles registration and login."""
        # Generate unique user for this locust user
        import uuid
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@test.com"
        self.user_password = "LoadTest123!"
        
        # Try to register (might already exist)
        self.client.post(
            "/api/auth/register",
            data={
                "username": self.user_email,
                "password": self.user_password,
            }
        )
        
        # Login
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": self.user_email,
                "password": self.user_password,
            }
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            # Try JSON login
            response = self.client.post(
                "/api/auth/login-json",
                json={
                    "email": self.user_email,
                    "password": self.user_password,
                }
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
    
    @property
    def auth_headers(self):
        """Get authorization headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(3)
    def health_check(self):
        """Check API health - high frequency task."""
        self.client.get("/health")
    
    @task(2)
    def analyze_text(self):
        """Analyze text - main user action."""
        text = random.choice(SAMPLE_TEXTS)
        
        response = self.client.post(
            "/api/analysis/",
            json={
                "text": text,
                "granularity": "sentence"
            },
            headers=self.auth_headers,
            name="/api/analysis/"
        )
        
        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            assert "overall_ai_probability" in data
            assert "segments" in data
    
    @task(1)
    def get_analytics(self):
        """Get user analytics."""
        self.client.get(
            "/api/analytics/",
            headers=self.auth_headers,
            name="/api/analytics/"
        )
    
    @task(1)
    def get_profile(self):
        """Get user profile/fingerprint info."""
        self.client.get(
            "/api/fingerprint/",
            headers=self.auth_headers,
            name="/api/fingerprint/"
        )


class HighLoadUser(HttpUser):
    """Simulates high-frequency API usage for stress testing."""
    
    wait_time = between(0.1, 0.5)
    token = None
    
    def on_start(self):
        """Quick login for high-load testing."""
        import uuid
        email = f"stress_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register
        self.client.post(
            "/api/auth/register",
            data={"username": email, "password": "StressTest123!"}
        )
        
        # Login
        response = self.client.post(
            "/api/auth/login-json",
            json={"email": email, "password": "StressTest123!"}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(5)
    def rapid_health_check(self):
        """Rapid health checks to test throughput."""
        self.client.get("/health")
    
    @task(2)
    def rapid_analysis(self):
        """Rapid text analysis."""
        self.client.post(
            "/api/analysis/",
            json={
                "text": "Quick test text for load testing purposes.",
                "granularity": "sentence"
            },
            headers=self.auth_headers,
            name="/api/analysis/ (rapid)"
        )


# Event handlers for reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, **kwargs):
    """Log request metrics."""
    pass  # Can add custom logging here


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("Load test starting...")


@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when test ends."""
    print("Load test completed.")
