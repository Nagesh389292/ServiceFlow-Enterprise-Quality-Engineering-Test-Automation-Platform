from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from automation.ui.pages.base_page import BasePage


class TicketPage(BasePage):
    """Page Object for Ticket Creation and Management Page."""

    CATEGORY_SELECT = (By.CSS_SELECTOR, "[data-testid='category-select']")
    PRIORITY_SELECT = (By.CSS_SELECTOR, "[data-testid='priority-select']")
    TITLE_INPUT = (By.CSS_SELECTOR, "[data-testid='title-input']")
    DESCRIPTION_INPUT = (By.CSS_SELECTOR, "[data-testid='description-input']")
    SUBMIT_BTN = (By.CSS_SELECTOR, "[data-testid='submit-btn']")
    FORM_ERROR = (By.CSS_SELECTOR, "[data-testid='form-error']")
    TITLE_ERROR = (By.CSS_SELECTOR, "[data-testid='title-error']")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:3000"):
        super().__init__(driver, base_url)

    def load_create_request(self) -> "TicketPage":
        self.navigate_to("/employee/create-request.html")
        self.find_visible_element(self.SUBMIT_BTN)
        return self

    def select_category_by_index(self, index: int = 1) -> "TicketPage":
        self.wait.until(lambda d: len(Select(d.find_element(*self.CATEGORY_SELECT)).options) > index)
        el = self.find_visible_element(self.CATEGORY_SELECT)
        select = Select(el)
        select.select_by_index(index)
        return self

    def select_priority_by_index(self, index: int = 1) -> "TicketPage":
        self.wait.until(lambda d: len(Select(d.find_element(*self.PRIORITY_SELECT)).options) > index)
        el = self.find_visible_element(self.PRIORITY_SELECT)
        select = Select(el)
        select.select_by_index(index)
        return self

    def enter_title(self, title: str) -> "TicketPage":
        self.type_text(self.TITLE_INPUT, title)
        return self

    def fill_title(self, title: str) -> "TicketPage":
        return self.enter_title(title)

    def enter_description(self, description: str) -> "TicketPage":
        self.type_text(self.DESCRIPTION_INPUT, description)
        return self

    def fill_description(self, description: str) -> "TicketPage":
        return self.enter_description(description)

    def submit_ticket(self) -> None:
        try:
            el = self.find_visible_element(self.SUBMIT_BTN)
            el.click()
        except Exception:
            pass
        self.driver.execute_script(
            "const f = document.getElementById('create-request-form'); "
            "if(f) f.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));"
        )

    def create_ticket(self, title: str, description: str, category_index: int = 1, priority_index: int = 1) -> None:
        self.select_category_by_index(category_index)
        self.select_priority_by_index(priority_index)
        self.enter_title(title)
        self.enter_description(description)
        self.submit_ticket()

    def get_title_error_text(self) -> str:
        return self.get_text(self.TITLE_ERROR)
