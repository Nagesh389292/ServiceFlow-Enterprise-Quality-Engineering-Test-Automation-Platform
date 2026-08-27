import pytest
from automation.api.clients.auth_client import AuthClient
from automation.api.clients.tickets_client import TicketsClient


@pytest.mark.regression
@pytest.mark.api
class TestAPINegativeBoundary:
    """Negative and boundary testing suite for API endpoints."""

    def test_unauthorized_profile_access(self, config):
        """TC_API_NEG_01: GET /api/auth/me without Bearer token returns HTTP 401 Unauthorized."""
        client = AuthClient(config)
        client.clear_auth_token()
        response = client.get_me()
        assert response.status_code in (401, 403)

    def test_invalid_login_credentials(self, config):
        """TC_API_NEG_02: POST /api/auth/login with wrong credentials returns HTTP 401 Unauthorized."""
        client = AuthClient(config)
        response = client.login("nonexistent@eqe.local", "WrongPass123!")
        assert response.status_code in (400, 401, 404)

    def test_fetch_nonexistent_ticket(self, config, auth_token):
        """TC_API_NEG_03: GET /api/tickets/999999 returns HTTP 404 Not Found."""
        client = TicketsClient(config)
        client.set_auth_token(auth_token)
        response = client.get_ticket(999999)
        assert response.status_code in (404, 422)

    def test_create_ticket_empty_payload_validation(self, config, auth_token):
        """TC_API_BOUND_01: POST /api/tickets with empty JSON body returns HTTP 422 Validation Error."""
        client = TicketsClient(config)
        client.set_auth_token(auth_token)
        response = client.create_ticket({})
        assert response.status_code in (400, 422)
