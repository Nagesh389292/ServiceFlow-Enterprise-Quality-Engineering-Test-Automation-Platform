import pytest
from automation.ui.pages.login_page import LoginPage
from automation.ui.pages.dashboard_page import DashboardPage


@pytest.mark.smoke
@pytest.mark.ui
class TestUISmoke:
    """Smoke test suite validating UI availability, login functionality, and page loads."""

    def test_login_page_renders(self, driver, config):
        """TC_UI_SMOKE_01: Verify login page loads successfully."""
        login_page = LoginPage(driver, config.base_url).load()
        assert login_page.is_element_displayed(login_page.USERNAME_INPUT)
        assert login_page.is_element_displayed(login_page.PASSWORD_INPUT)
        assert login_page.is_element_displayed(login_page.LOGIN_BUTTON)

    def test_valid_employee_login(self, driver, config):
        """TC_UI_SMOKE_02: Verify successful login with employee demo credentials."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("employee", "Employee@123")

        dashboard_page = DashboardPage(driver, config.base_url)
        assert dashboard_page.is_element_displayed(dashboard_page.MAIN_CONTENT)

    def test_invalid_login_error_message(self, driver, config):
        """TC_UI_SMOKE_03: Verify error message displayed on invalid login attempt."""
        login_page = LoginPage(driver, config.base_url).load()
        login_page.login_as("invalid_user", "WrongPassword123")
        assert login_page.is_login_error_visible()
