import os
import time
from typing import Tuple, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from automation.utilities.logger import get_logger

logger = get_logger("BasePage")


class BasePage:
    """Base Page Object class encapsulating Selenium WebDriver explicit waits and actions."""

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:3000", timeout: int = 10):
        self.driver = driver
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.wait = WebDriverWait(self.driver, self.timeout)

    def navigate_to(self, path: str = "") -> None:
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def find_element(self, locator: Tuple[By, str], timeout: int = None) -> WebElement:
        t = timeout if timeout is not None else self.timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            logger.error(f"Element not found within {t}s: {locator}")
            raise

    def find_visible_element(self, locator: Tuple[By, str], timeout: int = None) -> WebElement:
        t = timeout if timeout is not None else self.timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located(locator)
            )
        except TimeoutException:
            logger.error(f"Element not visible within {t}s: {locator}")
            raise

    def click(self, locator: Tuple[By, str]) -> None:
        logger.info(f"Clicking element: {locator}")
        el = self.wait.until(EC.element_to_be_clickable(locator))
        try:
            el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)

    def type_text(self, locator: Tuple[By, str], text: str, clear_first: bool = True) -> None:
        logger.info(f"Typing '{text}' into element: {locator}")
        el = self.find_visible_element(locator)
        try:
            el.click()
        except Exception:
            pass
        if clear_first:
            el.clear()
        el.send_keys(text)
        if not el.get_attribute("value"):
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; "
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true})); "
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                el, text
            )

    def get_text(self, locator: Tuple[By, str]) -> str:
        el = self.find_visible_element(locator)
        return el.text.strip()

    def is_element_displayed(self, locator: Tuple[By, str], timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_for_url_contains(self, url_part: str, timeout: int = 10) -> bool:
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.url_contains(url_part)
            )
        except TimeoutException:
            logger.error(f"URL did not contain '{url_part}' within {timeout}s. Current URL: {self.driver.current_url}")
            return False

    def take_screenshot(self, name: str = "screenshot") -> str:
        logs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs", "screenshots")
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(logs_dir, f"{name}_{timestamp}.png")
        self.driver.save_screenshot(filepath)
        logger.info(f"Saved screenshot to {filepath}")
        return filepath
