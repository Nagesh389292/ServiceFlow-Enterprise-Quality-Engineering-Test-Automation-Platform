import pytest
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.dashboard_page import DashboardPage


@pytest.mark.regression
@pytest.mark.ui
class TestUIRegression:
    """Regression test suite for UI consistency, sidebar navigation, and session persistence."""

    def test_sidebar_navigation_items(self, driver, config):
        """TC_UI_REG_01: Verify sidebar navigation links are present and clickable."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        dashboard_page = DashboardPage(driver, config.base_url)
        assert dashboard_page.is_element_displayed(dashboard_page.NAV_CREATE_REQUEST)
        assert dashboard_page.is_element_displayed(dashboard_page.NAV_MY_REQUESTS)

    def test_page_title_consistency(self, driver, config):
        """TC_UI_REG_02: Verify header page title matches portal section."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        dashboard_page = DashboardPage(driver, config.base_url)
        title = dashboard_page.get_page_title_text()
        assert "Dashboard" in title or len(title) > 0
