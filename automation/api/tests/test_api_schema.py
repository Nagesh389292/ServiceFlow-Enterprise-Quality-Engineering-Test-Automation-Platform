"""
API Contract / Schema Validation Test Suite
TC_API_SCHEMA_01 – TC_API_SCHEMA_05

Validates every critical API endpoint against its JSON schema:
- HTTP status codes
- Required fields presence
- Data types correctness
- Enum value constraints
- Response headers
"""
import pytest
import jsonschema
from automation.api.clients.auth_client import AuthClient
from automation.api.clients.tickets_client import TicketsClient
from automation.api.schemas.auth_schema import LOGIN_RESPONSE_SCHEMA, USER_PROFILE_SCHEMA, CATEGORY_LIST_SCHEMA
from automation.api.schemas.ticket_schema import TICKET_CREATE_SCHEMA, TICKET_GET_SCHEMA
from automation.utilities.helpers import TestDataGenerator


def validate_schema(data: dict, schema: dict, label: str) -> None:
    """Helper: raises AssertionError with detailed message on schema violation."""
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        raise AssertionError(
            f"[{label}] JSON Schema Violation:\n"
            f"  Field:   {' -> '.join(str(p) for p in exc.absolute_path) or 'root'}\n"
            f"  Message: {exc.message}\n"
            f"  Value:   {exc.instance!r}"
        ) from exc


@pytest.mark.regression
@pytest.mark.api
class TestAPISchema:
    """TC_API_SCHEMA: Contract/Schema validation suite — HTTP status, fields, types, enums, headers."""

    # ------------------------------------------------------------------
    # TC_API_SCHEMA_01: Login token response contract
    # ------------------------------------------------------------------
    def test_login_token_schema(self, config):
        """TC_API_SCHEMA_01: POST /api/auth/login response matches login schema contract."""
        client = AuthClient(config)
        response = client.login("admin@eqe.com", "Admin@123")

        assert response.status_code == 200, (
            f"Expected HTTP 200 but got {response.status_code}: {response.text[:200]}"
        )

        data = response.json()
        validate_schema(data, LOGIN_RESPONSE_SCHEMA, "LoginResponse")

        # Validate token_type is case-insensitively 'bearer'
        assert data["token_type"].lower() == "bearer", (
            f"token_type must be 'bearer', got: {data['token_type']!r}"
        )
        # Validate access_token is a non-trivial JWT (3 dot-separated parts)
        parts = data["access_token"].split(".")
        assert len(parts) == 3, (
            f"access_token does not look like a JWT (expected 3 parts, got {len(parts)})"
        )

    # ------------------------------------------------------------------
    # TC_API_SCHEMA_02: User profile response contract
    # ------------------------------------------------------------------
    def test_user_profile_schema(self, config, auth_token):
        """TC_API_SCHEMA_02: GET /api/auth/me response matches user profile schema contract."""
        client = AuthClient(config)
        client.set_auth_token(auth_token)
        response = client.get_me()

        assert response.status_code == 200, (
            f"Expected HTTP 200 but got {response.status_code}"
        )

        data = response.json()
        validate_schema(data, USER_PROFILE_SCHEMA, "UserProfile")

        # Extra assertion: role must be a known system role
        assert data["role"] in ("admin", "agent", "employee", "support"), (
            f"Unexpected role value: {data['role']!r}"
        )

    # ------------------------------------------------------------------
    # TC_API_SCHEMA_03: Ticket create response contract
    # ------------------------------------------------------------------
    def test_create_ticket_response_schema(self, config, auth_token):
        """TC_API_SCHEMA_03: POST /api/tickets response matches ticket schema — all required fields + correct types."""
        client = TicketsClient(config)
        client.set_auth_token(auth_token)

        payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=2)
        response = client.create_ticket(payload)

        assert response.status_code in (200, 201), (
            f"Expected HTTP 200/201 but got {response.status_code}: {response.text[:300]}"
        )

        data = response.json()
        validate_schema(data, TICKET_CREATE_SCHEMA, "TicketCreate")

        # Validate title echoed correctly
        assert data["title"] == payload["title"], (
            f"Returned title {data['title']!r} ≠ submitted title {payload['title']!r}"
        )
        # Validate id is a positive integer
        assert isinstance(data["id"], int) and data["id"] > 0, (
            f"id must be a positive integer, got: {data['id']!r}"
        )

    # ------------------------------------------------------------------
    # TC_API_SCHEMA_04: Ticket status enum validation
    # ------------------------------------------------------------------
    def test_ticket_status_is_valid_enum(self, config, auth_token):
        """TC_API_SCHEMA_04: POST /api/tickets response status field value is a valid enum member."""
        client = TicketsClient(config)
        client.set_auth_token(auth_token)

        payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=1)
        response = client.create_ticket(payload)
        assert response.status_code in (200, 201)

        data = response.json()
        valid_statuses = {"open", "in_progress", "resolved", "closed", "pending"}
        assert data.get("status") in valid_statuses, (
            f"status {data.get('status')!r} is not a valid enum value. "
            f"Allowed: {valid_statuses}"
        )

    # ------------------------------------------------------------------
    # TC_API_SCHEMA_05: Response headers contract
    # ------------------------------------------------------------------
    def test_api_response_headers_contract(self, config, auth_token):
        """TC_API_SCHEMA_05: API endpoints return correct Content-Type header."""
        client = AuthClient(config)
        client.set_auth_token(auth_token)
        response = client.get_me()

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Expected 'application/json' in Content-Type header, got: {content_type!r}"
        )
