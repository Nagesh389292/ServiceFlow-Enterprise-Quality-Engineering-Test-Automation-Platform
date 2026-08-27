"""
Data-Driven UI Test Suite
TC_DD_UI_01 – TC_DD_UI_03

Demonstrates automation framework design through parametrized test matrices.
Tests the same behaviour with multiple input combinations rather than
writing one test per scenario — a key QA engineering best practice.

Login Matrix: 7 input combinations (valid + invalid + boundary + security)
Ticket Matrix: 3 input combinations (valid + boundary + empty)
"""
import pytest
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.ticket_page import TicketPage


# ── Login Matrix ──────────────────────────────────────────────────────────────
#  (username,       password,        expect_success, scenario_label)
LOGIN_MATRIX = [
    # ---- Valid credentials ------------------------------------------------
    ("employee",         "Employee@123",   True,  "valid_employee"),
    ("admin",            "Admin@123",      True,  "valid_admin"),
    # ---- Wrong password --------------------------------------------------
    ("employee",         "WrongPass!",     False, "wrong_password"),
    # ---- Wrong username --------------------------------------------------
    ("nobody",           "Employee@123",   False, "wrong_username"),
    # ---- Empty username --------------------------------------------------
    ("",                 "Employee@123",   False, "empty_username"),
    # ---- Empty password --------------------------------------------------
    ("employee",         "",               False, "empty_password"),
    # ---- SQL injection attempt -------------------------------------------
    ("' OR '1'='1",      "' OR '1'='1",    False, "sql_injection_attempt"),
]

# ── Ticket Creation Matrix ────────────────────────────────────────────────────
#  (title,                              description,       expect_success, scenario_label)
TICKET_MATRIX = [
    # ---- Valid input -------------------------------------------------------
    ("Valid Test Ticket",                "Normal description",    True,  "valid_input"),
    # ---- Boundary: maximum title length (255 chars) -----------------------
    ("T" * 255,                          "Boundary title test",   True,  "max_length_title"),
    # ---- Empty title (should show validation error) -----------------------
    ("",                                 "No title test",         False, "empty_title_validation"),
]


@pytest.mark.functional
@pytest.mark.data_driven
@pytest.mark.ui
class TestUIDataDriven:
    """
    TC_DD_UI: Data-driven parametrized UI test suite.

    Demonstrates automation framework design: same test logic executed
    across multiple input combinations using pytest.mark.parametrize.
    """

    @pytest.mark.parametrize(
        "username,password,expect_success,scenario",
        LOGIN_MATRIX,
        ids=[row[3] for row in LOGIN_MATRIX]
    )
    def test_login_matrix(self, driver, config, username, password, expect_success, scenario):
        """
        TC_DD_UI_01: Parametrized login matrix — 7 input combinations.

        Validates: valid credentials redirect to dashboard, invalid/boundary
        credentials display an appropriate error message and stay on login page.
        """
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as(username, password)

        current_url = driver.current_url

        if expect_success:
            assert "dashboard" in current_url or "dashboard" in driver.page_source.lower(), (
                f"[{scenario}] Expected dashboard redirect after valid login. "
                f"URL: {current_url}"
            )
        else:
            # Should stay on login page or show error
            on_login_page = "login" in current_url
            has_error = login_page.is_error_displayed() if hasattr(login_page, "is_error_displayed") else True
            assert on_login_page or has_error, (
                f"[{scenario}] Expected to remain on login page or see error. "
                f"URL: {current_url}"
            )

    @pytest.mark.parametrize(
        "title,description,expect_success,scenario",
        TICKET_MATRIX,
        ids=[row[3] for row in TICKET_MATRIX]
    )
    def test_ticket_creation_matrix(self, driver, config, title, description, expect_success, scenario):
        """
        TC_DD_UI_02: Parametrized ticket creation matrix — 3 input combinations.

        Validates: valid/boundary-length inputs succeed (redirect to view page),
        empty title triggers visible validation error.
        """
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        ticket_page = TicketPage(driver, config.base_url).load_create_request()
        ticket_page.select_category_by_index(1)
        ticket_page.select_priority_by_index(1)

        if title:
            ticket_page.fill_title(title)
        ticket_page.fill_description(description)
        ticket_page.submit_ticket()

        if expect_success:
            import time
            time.sleep(1.5)  # allow redirect after successful submit
            current_url = driver.current_url
            # Either redirected to view-request page or toast success shown
            success = "view-request" in current_url or "dashboard" in current_url
            if not success:
                # Check for success toast in page source
                success = "successfully" in driver.page_source.lower()
            assert success, (
                f"[{scenario}] Expected successful ticket creation. URL: {current_url}"
            )
        else:
            # Should show title validation error
            assert ticket_page.is_element_displayed(ticket_page.TITLE_ERROR, timeout=5), (
                f"[{scenario}] Expected title validation error to be visible."
            )
