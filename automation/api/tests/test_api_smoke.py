import pytest
from automation.api.clients.auth_client import AuthClient


@pytest.mark.smoke
@pytest.mark.api
class TestAPISmoke:
    """API Smoke test suite validating healthcheck, authentication, and status codes."""

    def test_healthcheck_endpoint(self, api_client):
        """TC_API_SMOKE_01: GET /health returns 200 OK and healthy status."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_auth_login_token_generation(self, config):
        """TC_API_SMOKE_02: POST /api/auth/login returns valid OAuth2 JWT bearer token."""
        client = AuthClient(config)
        response = client.login("admin@eqe.com", "Admin@123")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
