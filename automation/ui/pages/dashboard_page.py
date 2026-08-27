from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from automation.ui.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page Object for Employee/Admin Dashboard Page."""

    PAGE_TITLE = (By.CSS_SELECTOR, "[data-testid='page-title']")
    SIDEBAR = (By.CSS_SELECTOR, "[data-testid='sidebar']")
    USER_NAME = (By.CSS_SELECTOR, "[data-testid='user-name']")
    USER_ROLE = (By.CSS_SELECTOR, "[data-testid='user-role']")
    LOGOUT_BTN = (By.CSS_SELECTOR, "[data-testid='logout-btn']")
    NAV_CREATE_REQUEST = (By.CSS_SELECTOR, "[data-testid='nav-create-request']")
    NAV_MY_REQUESTS = (By.CSS_SELECTOR, "[data-testid='nav-my-requests']")
    MAIN_CONTENT = (By.CSS_SELECTOR, "[data-testid='main-content']")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:3000"):
        super().__init__(driver, base_url)

    def load(self, role: str = "employee") -> "DashboardPage":
        self.navigate_to(f"/{role}/dashboard.html")
        return self

    def get_page_title_text(self) -> str:
        return self.get_text(self.PAGE_TITLE)

    def get_logged_in_username(self) -> str:
        return self.get_text(self.USER_NAME)

    def get_user_role(self) -> str:
        return self.get_text(self.USER_ROLE)

    def click_create_request_nav(self) -> None:
        el = self.find_visible_element(self.NAV_CREATE_REQUEST)
        href = el.get_attribute("href")
        if href:
            self.driver.get(href)
        else:
            self.click(self.NAV_CREATE_REQUEST)

    def click_logout(self) -> None:
        self.driver.execute_script("localStorage.clear(); window.location.href = '/shared/login.html';")
        self.wait_for_url_contains("login.html", timeout=10)
