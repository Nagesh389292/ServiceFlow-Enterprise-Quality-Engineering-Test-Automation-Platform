"""
End-to-End Cross-Layer Validation Test Suite
TC_E2E_01 – TC_E2E_03

Validates a complete user journey across all three application layers:
  UI (Selenium) → REST API (requests) → Database (SQLite/PostgreSQL)

This is the strongest possible QE demonstration: proving that a single
user action (e.g. creating a ticket) produces consistent, correct state
across every layer of the application stack.
"""
import time
import pytest
from automation.api.clients.auth_client import AuthClient
from automation.api.clients.tickets_client import TicketsClient
from automation.database.db_client import DatabaseClient
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.ticket_page import TicketPage
from automation.utilities.helpers import TestDataGenerator
from automation.utilities.logger import get_logger

logger = get_logger("E2ETests")


@pytest.mark.functional
@pytest.mark.regression
class TestE2ETicketLifecycle:
    """
    TC_E2E: End-to-end cross-layer ticket lifecycle validation.

    Proves UI → API → DB consistency: a ticket submitted via the browser
    must be retrievable via the REST API and persisted correctly in the
    database with valid FK relationships and timestamps.
    """

    # ------------------------------------------------------------------
    # TC_E2E_01 — UI creates ticket → API confirms → DB validates
    # ------------------------------------------------------------------
    def test_e2e_create_ticket_ui_verify_api_db(self, driver, config, auth_token, db_client):
        """
        TC_E2E_01: Full cross-layer ticket creation.

        Steps:
          1. Employee logs in via Selenium (UI layer)
          2. Navigates to Create Request page
          3. Fills in title + description + category + priority, submits
          4. API confirms the ticket exists with correct data
          5. DB confirms the record row with correct FK, status, timestamp
        """
        title = f"E2E-Ticket-{TestDataGenerator.random_string(6)}"
        description = "Cross-layer E2E validation test — automated"

        # ---- Layer 1: UI — Create ticket via Selenium ----
        logger.info(f"[E2E_01] Step 1 — UI: Creating ticket '{title}'")
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        ticket_page = TicketPage(driver, config.base_url).load_create_request()
        ticket_page.select_category_by_index(1)
        ticket_page.select_priority_by_index(1)
        ticket_page.fill_title(title)
        ticket_page.fill_description(description)
        ticket_page.submit_ticket()

        # Allow time for async fetchWithAuth and DB write
        time.sleep(3.0)

        # ---- Layer 2: API — Confirm ticket was created ----
        logger.info("[E2E_01] Step 2 — API: Fetching tickets to verify creation")
        api_client = TicketsClient(config)
        api_client.set_auth_token(auth_token)

        tickets_resp = api_client.get_tickets()
        assert tickets_resp.status_code == 200, f"GET /api/tickets failed: {tickets_resp.text}"

        tickets_data = tickets_resp.json()
        # Handle both list and paginated response shapes
        if isinstance(tickets_data, list):
            tickets_list = tickets_data
        else:
            tickets_list = tickets_data.get("items", tickets_data.get("data", []))

        matching = [t for t in tickets_list if t.get("title") == title]
        assert len(matching) >= 1, (
            f"[E2E_01] API did not return ticket with title '{title}'. "
            f"Found {len(tickets_list)} tickets total."
        )
        ticket_id = matching[0]["id"]
        logger.info(f"[E2E_01] API confirmed ticket id={ticket_id}")

        # ---- Layer 3: DB — Validate record with FK/timestamp integrity ----
        logger.info("[E2E_01] Step 3 — DB: Validating database record")
        rows = db_client.execute_query(
            "SELECT id, title, status, category_id, priority_id, created_at FROM tickets WHERE id = ?",
            (ticket_id,)
        )
        assert len(rows) == 1, (
            f"[E2E_01] Expected 1 DB row for ticket id={ticket_id}, found {len(rows)}"
        )
        row = rows[0]

        assert row["title"] == title, (
            f"[E2E_01] DB title mismatch: {row['title']!r} ≠ {title!r}"
        )
        assert row["status"].lower() in ("open", "in_progress", "pending"), (
            f"[E2E_01] Unexpected status in DB: {row['status']!r}"
        )
        assert row["category_id"] is not None, "[E2E_01] DB category_id is NULL — FK broken"
        assert row["priority_id"] is not None, "[E2E_01] DB priority_id is NULL — FK broken"
        assert row["created_at"] is not None, "[E2E_01] DB created_at timestamp is NULL"

        logger.info(f"[E2E_01] PASS — Ticket id={ticket_id} verified across UI + API + DB ✓")

    # ------------------------------------------------------------------
    # TC_E2E_02 — API updates status → DB reflects change
    # ------------------------------------------------------------------
    def test_e2e_ticket_status_propagation(self, config, auth_token, db_client):
        """
        TC_E2E_02: Ticket status update via API propagates correctly to database.

        Steps:
          1. Create a ticket via API
          2. Update ticket status via PUT /api/tickets/{id}
          3. DB confirms the updated status reflects immediately
        """
        # ---- Create ticket via API ----
        client = TicketsClient(config)
        client.set_auth_token(auth_token)

        payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=2)
        create_resp = client.create_ticket(payload)
        assert create_resp.status_code in (200, 201), (
            f"[E2E_02] Ticket creation failed: {create_resp.text}"
        )
        ticket_id = create_resp.json()["id"]
        logger.info(f"[E2E_02] Created ticket id={ticket_id}")

        # ---- Update ticket status via API ----
        update_resp = client.update_ticket(ticket_id, {"status": "in_progress"})
        # Accept 200 or 403 (employee may not update — admin token is needed)
        if update_resp.status_code == 403:
            # Re-authenticate as admin
            auth_client = AuthClient(config)
            admin_resp = auth_client.login("admin@eqe.com", "Admin@123")
            admin_token = admin_resp.json()["access_token"]
            client.set_auth_token(admin_token)
            update_resp = client.update_ticket(ticket_id, {"status": "in_progress"})

        assert update_resp.status_code in (200, 204), (
            f"[E2E_02] Status update failed (HTTP {update_resp.status_code}): {update_resp.text}"
        )
        logger.info(f"[E2E_02] API updated ticket id={ticket_id} to in_progress")

        # ---- DB confirms updated status ----
        rows = db_client.execute_query(
            "SELECT id, status FROM tickets WHERE id = ?", (ticket_id,)
        )
        assert len(rows) == 1, f"[E2E_02] DB row not found for id={ticket_id}"
        assert rows[0]["status"].lower() == "in_progress", (
            f"[E2E_02] DB status not updated: expected 'in_progress', got {rows[0]['status']!r}"
        )
        logger.info(f"[E2E_02] PASS — Status 'in_progress' confirmed in DB ✓")

    # ------------------------------------------------------------------
    # TC_E2E_03 — Full Quality Gate: all three layers healthy
    # ------------------------------------------------------------------
    def test_e2e_quality_gate_smoke(self, driver, config, db_client):
        """
        TC_E2E_03: Quality Gate — validates all three application layers are healthy.

        This test simulates a pre-release quality gate check:
          - API layer: health endpoint responds 200
          - UI layer: login page renders and accepts valid credentials
          - DB layer: seed data (categories + priorities) present and intact

        ALL THREE must pass for the quality gate to be APPROVED.
        """
        gate_results = {}

        # ---- Gate 1: API health check ----
        logger.info("[E2E_03] Quality Gate — Checking API layer...")
        auth_client = AuthClient(config)
        health_resp = auth_client.get("/health")
        gate_results["api_health"] = health_resp.status_code == 200
        assert gate_results["api_health"], (
            f"[QualityGate] FAIL — API health check returned HTTP {health_resp.status_code}"
        )
        logger.info("[E2E_03] API layer: PASS ✓")

        # ---- Gate 2: UI login smoke ----
        logger.info("[E2E_03] Quality Gate — Checking UI layer...")
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("admin", "Admin@123")
        current_url = driver.current_url
        gate_results["ui_login"] = "dashboard" in current_url
        assert gate_results["ui_login"], (
            f"[QualityGate] FAIL — UI login did not reach dashboard. URL: {current_url}"
        )
        logger.info("[E2E_03] UI layer: PASS ✓")

        # ---- Gate 3: DB seed integrity ----
        logger.info("[E2E_03] Quality Gate — Checking DB layer...")
        cats = db_client.execute_query("SELECT COUNT(*) as cnt FROM categories WHERE is_active = 1")
        prios = db_client.execute_query("SELECT COUNT(*) as cnt FROM priorities WHERE is_active = 1")
        cat_count = cats[0]["cnt"] if cats else 0
        prio_count = prios[0]["cnt"] if prios else 0
        gate_results["db_seed"] = cat_count >= 1 and prio_count >= 1
        assert gate_results["db_seed"], (
            f"[QualityGate] FAIL — DB seed data missing. "
            f"Categories: {cat_count}, Priorities: {prio_count}"
        )
        logger.info(f"[E2E_03] DB layer: PASS ✓ ({cat_count} categories, {prio_count} priorities)")

        # ---- Quality Gate Summary ----
        all_passed = all(gate_results.values())
        logger.info(
            f"\n{'='*50}\n"
            f"  QUALITY GATE RESULT\n"
            f"{'='*50}\n"
            f"  API Health:  {'PASS ✓' if gate_results['api_health'] else 'FAIL ✗'}\n"
            f"  UI Login:    {'PASS ✓' if gate_results['ui_login'] else 'FAIL ✗'}\n"
            f"  DB Seed:     {'PASS ✓' if gate_results['db_seed'] else 'FAIL ✗'}\n"
            f"{'='*50}\n"
            f"  RESULT: {'✅ RELEASE APPROVED' if all_passed else '❌ RELEASE BLOCKED'}\n"
            f"{'='*50}"
        )
        assert all_passed, "[QualityGate] One or more gates failed — release blocked."
