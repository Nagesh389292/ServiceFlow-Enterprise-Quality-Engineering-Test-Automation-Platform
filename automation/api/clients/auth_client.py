from typing import Dict, Any
import requests
from automation.api.clients.base_api_client import BaseAPIClient


class AuthClient(BaseAPIClient):
    """API Client for Authentication endpoints (/api/auth)."""

    def login(self, username_or_email: str = "employee@eqe.com", password: str = "Employee@123") -> requests.Response:
        """Requests OAuth2 JWT token via form URL encoded payload."""
        payload = {
            "username": username_or_email,
            "password": password
        }
        # OAuth2 password request uses form-urlencoded
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self.post("/api/auth/login", data=payload, headers=headers)

    def register(self, user_data: Dict[str, Any]) -> requests.Response:
        """Registers a new user."""
        return self.post("/api/auth/register", json=user_data)

    def get_me(self) -> requests.Response:
        """Fetches profile info of authenticated user."""
        return self.get("/api/auth/me")
