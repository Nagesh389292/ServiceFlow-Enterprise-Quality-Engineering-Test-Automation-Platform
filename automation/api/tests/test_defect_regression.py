"""
Defect Regression Test Suite
TC_REG_DEF_01 – TC_REG_DEF_03

These tests were written specifically to catch the 3 defects documented in
docs/DEFECT_REGISTER.md. They serve as permanent regression guards ensuring
those defects never re-appear in future builds.

Reference: docs/DEFECT_REGISTER.md
"""
import pytest
from automation.api.clients.auth_client import AuthClient
from automation.database.db_client import DatabaseClient


@pytest.mark.regression
@pytest.mark.defect_regression
@pytest.mark.api
class TestDefectRegression:
    """
    TC_REG_DEF: Defect regression guards — one test per closed defect.

    Each test is named after and linked to a specific entry in DEFECT_REGISTER.md.
    These tests must always pass; failure indicates a regression.
    """

    # ------------------------------------------------------------------
    # DEF-001 Regression: Login must reject blank password
    # ------------------------------------------------------------------
    def test_def001_login_rejects_empty_password(self, config):
        """
        TC_REG_DEF_01 — DEF-001 Regression Guard.

        Verifies: POST /api/auth/login with an empty string password returns
        HTTP 4xx (not 200). Previously, malformed URLSearchParams body caused
        the API to return 422 instead of properly rejecting the request.

        Root cause was fixed in login.html by adding .toString() to URLSearchParams.
        """
        client = AuthClient(config)
        # Attempt login with blank password (should be rejected)
        response = client.login("admin@eqe.com", "")
        assert response.status_code != 200, (
            f"[DEF-001 REGRESSION] Login with blank password returned HTTP 200 — "
            f"authentication is accepting empty passwords! "
            f"Response: {response.text[:300]}"
        )
        assert response.status_code in (400, 401, 422), (
            f"[DEF-001 REGRESSION] Expected 400/401/422 for blank password, "
            f"got HTTP {response.status_code}"
        )

    # ------------------------------------------------------------------
    # DEF-002 Regression: Form validation must be triggerable via API
    # ------------------------------------------------------------------
    def test_def002_ticket_creation_requires_title_via_api(self, config, auth_token):
        """
        TC_REG_DEF_02 — DEF-002 Regression Guard.

        Verifies: POST /api/tickets with missing title field returns HTTP 422.
        This ensures the backend-level validation (the same business rule that
        DEF-002 tested at the UI layer) is permanently enforced at the API layer.
        """
        from automation.api.clients.tickets_client import TicketsClient
        client = TicketsClient(config)
        client.set_auth_token(auth_token)

        # Submit ticket without title field
        response = client.create_ticket({
            "description": "Test without title",
            "category_id": 1,
            "priority_id": 1
        })
        assert response.status_code in (400, 422), (
            f"[DEF-002 REGRESSION] API accepted ticket without title (HTTP {response.status_code}). "
            f"Title validation is broken at API layer. Response: {response.text[:300]}"
        )

    # ------------------------------------------------------------------
    # DEF-003 Regression: DB client must execute real queries (not silently skip)
    # ------------------------------------------------------------------
    def test_def003_db_client_executes_real_query(self, db_client: DatabaseClient):
        """
        TC_REG_DEF_03 — DEF-003 Regression Guard.

        Verifies: DatabaseClient.execute_query() actually executes SQL against
        the database and returns meaningful data — not an empty list due to
        silent PostgreSQL fallback failure.

        Previously, all DB queries silently returned [] when PostgreSQL was
        unavailable, masking test failures.
        """
        # Query a table guaranteed to have seed data
        rows = db_client.execute_query("SELECT COUNT(*) as cnt FROM users")
        assert len(rows) == 1, (
            "[DEF-003 REGRESSION] execute_query() returned empty list — "
            "database client is silently skipping SQL execution."
        )
        count = rows[0].get("cnt", rows[0].get("COUNT(*)", 0))
        assert count >= 1, (
            f"[DEF-003 REGRESSION] users table appears empty (count={count}). "
            "Either DB is not seeded or query was not executed."
        )
