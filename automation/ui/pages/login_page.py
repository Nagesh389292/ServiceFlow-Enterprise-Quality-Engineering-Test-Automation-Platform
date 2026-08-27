from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from automation.ui.pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object representing the Enterprise Service Portal Login Page."""

    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "[data-testid='username-input']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "[data-testid='password-input']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "[data-testid='login-button']")
    REMEMBER_CHECKBOX = (By.CSS_SELECTOR, "[data-testid='remember-checkbox']")
    LOGIN_ERROR = (By.CSS_SELECTOR, "[data-testid='login-error']")
    USERNAME_ERROR = (By.CSS_SELECTOR, "[data-testid='username-error']")
    PASSWORD_ERROR = (By.CSS_SELECTOR, "[data-testid='password-error']")
    DEMO_ADMIN_BTN = (By.CSS_SELECTOR, "[data-user='admin']")
    DEMO_AGENT_BTN = (By.CSS_SELECTOR, "[data-user='agent']")
    DEMO_EMPLOYEE_BTN = (By.CSS_SELECTOR, "[data-user='employee']")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:3000"):
        super().__init__(driver, base_url)

    def load(self) -> "LoginPage":
        self.navigate_to("/shared/login.html")
        try:
            self.driver.execute_script("window.localStorage.clear();")
        except Exception:
            pass
        return self

    def enter_username(self, username: str) -> "LoginPage":
        self.type_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_login(self) -> None:
        p_el = self.find_visible_element(self.PASSWORD_INPUT)
        p_el.send_keys(Keys.ENTER)

    def login_as(self, username: str, password: str, expect_success: bool = True) -> bool:
        """Attempt login. Returns True if dashboard reached, False if stayed on login page."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        try:
            self.wait_for_url_contains("dashboard", timeout=8)
            return True
        except Exception:
            return False

    def get_login_error_text(self) -> str:
        return self.get_text(self.LOGIN_ERROR)

    def is_login_error_visible(self) -> bool:
        return self.is_element_displayed(self.LOGIN_ERROR)

    def is_error_displayed(self) -> bool:
        """Returns True if any login error message (field or form level) is visible."""
        return (
            self.is_element_displayed(self.LOGIN_ERROR, timeout=3)
            or self.is_element_displayed(self.USERNAME_ERROR, timeout=1)
            or self.is_element_displayed(self.PASSWORD_ERROR, timeout=1)
        )
