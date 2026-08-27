import pytest
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.ticket_page import TicketPage


@pytest.mark.functional
@pytest.mark.ui
class TestUIFunctional:
    """Functional & Data-driven test suite for form validation, edge cases, and role access."""

    @pytest.mark.parametrize("username,password,role", [
        ("admin", "Admin@123", "admin"),
        ("agent", "Agent@123", "agent"),
        ("employee", "Employee@123", "employee")
    ])
    def test_multi_role_login(self, driver, config, username, password, role):
        """TC_UI_FUNC_01: Data-driven login verification for all system roles."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as(username, password)
        # Check current URL matches expected role portal
        current_url = driver.current_url
        assert role in current_url or "dashboard" in current_url

    def test_create_request_validation(self, driver, config):
        """TC_UI_FUNC_02: Verify mandatory field validation error triggers."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        ticket_page = TicketPage(driver, config.base_url).load_create_request()
        ticket_page.submit_ticket()

        assert ticket_page.is_element_displayed(ticket_page.TITLE_ERROR, timeout=5)
