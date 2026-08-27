import pytest
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.dashboard_page import DashboardPage
from automation.ui.pages.ticket_page import TicketPage


@pytest.mark.sanity
@pytest.mark.ui
class TestUISanity:
    """Sanity test suite validating critical end-to-end user workflows."""

    def test_create_service_request_navigation(self, driver, config):
        """TC_UI_SANITY_01: Verify navigation to Create Request form after login."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        dashboard_page = DashboardPage(driver, config.base_url)
        dashboard_page.click_create_request_nav()

        ticket_page = TicketPage(driver, config.base_url)
        assert ticket_page.is_element_displayed(ticket_page.TITLE_INPUT)
        assert ticket_page.is_element_displayed(ticket_page.DESCRIPTION_INPUT)

    def test_user_logout_workflow(self, driver, config):
        """TC_UI_SANITY_02: Verify user sign out invalidates session and redirects to login."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        dashboard_page = DashboardPage(driver, config.base_url)
        dashboard_page.click_logout()

        assert login_page.is_element_displayed(login_page.LOGIN_BUTTON, timeout=5)
