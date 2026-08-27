import pytest
from automation.api.clients.auth_client import AuthClient
from automation.api.clients.tickets_client import TicketsClient
from automation.utilities.helpers import TestDataGenerator


@pytest.mark.functional
@pytest.mark.api
class TestAPIFunctional:
    """API Functional test suite for user profile, category list, and ticket CRUD lifecycle."""

    def test_authenticated_user_profile(self, config, auth_token):
        """TC_API_FUNC_01: GET /api/auth/me returns profile info for authenticated token."""
        client = AuthClient(config)
        client.set_auth_token(auth_token)
        response = client.get_me()
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data

    def test_get_categories_list(self, config, auth_token):
        """TC_API_FUNC_02: GET /api/categories returns active ticket categories."""
        client = AuthClient(config)
        client.set_auth_token(auth_token)
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_ticket_lifecycle_create_and_fetch(self, config, auth_token):
        """TC_API_FUNC_03: Create a ticket via API and verify fetch response matching schema."""
        client = TicketsClient(config)
        client.set_auth_token(auth_token)

        payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=3)
        create_res = client.create_ticket(payload)
        assert create_res.status_code in (200, 201)
        created_ticket = create_res.json()
        assert created_ticket.get("title") == payload["title"]

        ticket_id = created_ticket.get("id")
        fetch_res = client.get_ticket(ticket_id)
        assert fetch_res.status_code == 200
        fetch_data = fetch_res.json()
        assert fetch_data.get("id") == ticket_id
