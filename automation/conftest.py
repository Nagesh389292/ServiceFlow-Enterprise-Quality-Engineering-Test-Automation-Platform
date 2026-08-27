import json
import os
import sys
import time
from pathlib import Path
from typing import Generator

# Ensure workspace root directory is in sys.path for absolute package imports
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from automation.configuration.config import Config

from automation.api.clients.base_api_client import BaseAPIClient
from automation.api.clients.auth_client import AuthClient
from automation.database.db_client import DatabaseClient
from automation.utilities.logger import get_logger

logger = get_logger("Conftest")

# ── Report directories ────────────────────────────────────────────────────────
_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
_SCREENSHOTS_DIR = os.path.join(_REPORTS_DIR, "screenshots")
_ARTIFACTS_DIR = os.path.join(_REPORTS_DIR, "artifacts")
_HTML_REPORT = os.path.join(_REPORTS_DIR, "html", "report.html")
_JSON_REPORT = os.path.join(_REPORTS_DIR, "json", "results.json")

for _d in (_SCREENSHOTS_DIR, _ARTIFACTS_DIR,
           os.path.dirname(_HTML_REPORT), os.path.dirname(_JSON_REPORT)):
    os.makedirs(_d, exist_ok=True)


# ── CLI Options ───────────────────────────────────────────────────────────────
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=os.getenv("ENV", "local"),
        help="Environment to run tests against: local, docker, ci"
    )


# ── Markers ───────────────────────────────────────────────────────────────────
def pytest_configure(config):
    """Register custom markers and set default HTML / JSON report paths."""
    config.addinivalue_line("markers", "smoke: Mark test as smoke test")
    config.addinivalue_line("markers", "sanity: Mark test as sanity test")
    config.addinivalue_line("markers", "functional: Mark test as functional test")
    config.addinivalue_line("markers", "regression: Mark test as regression test")
    config.addinivalue_line("markers", "ui: Mark test as UI automation test")
    config.addinivalue_line("markers", "api: Mark test as API automation test")
    config.addinivalue_line("markers", "database: Mark test as Database validation test")
    config.addinivalue_line("markers", "e2e: Mark test as end-to-end cross-layer test")
    config.addinivalue_line("markers", "data_driven: Mark test as data-driven parametrized test")
    config.addinivalue_line("markers", "defect_regression: Mark test as defect regression / re-test")
    config.addinivalue_line("markers", "performance: Mark test as performance / SLA benchmark test")


    # Auto-configure pytest-html report path (if plugin available)
    if not config.option.__dict__.get("htmlpath"):
        try:
            config.option.htmlpath = _HTML_REPORT
            config.option.self_contained_html = True
        except AttributeError:
            pass  # plugin not installed — skip


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def config(request) -> Config:
    env_name = request.config.getoption("--env")
    logger.info(f"Loaded configuration profile for environment: {env_name}")
    return Config(env=env_name)


@pytest.fixture(scope="function")
def driver(config: Config) -> Generator[WebDriver, None, None]:
    """WebDriver fixture managing browser lifecycle with options."""
    options = ChromeOptions()
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Enable browser console log capture
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver_instance = webdriver.Chrome(options=options)
    driver_instance.implicitly_wait(config.implicit_wait)
    logger.info("Initialized Chrome WebDriver session.")

    yield driver_instance

    logger.info("Closing Chrome WebDriver session.")
    driver_instance.quit()


@pytest.fixture(scope="session")
def api_client(config: Config) -> BaseAPIClient:
    return BaseAPIClient(config)


@pytest.fixture(scope="session")
def auth_token(config: Config) -> str:
    """Session-scoped fixture obtaining JWT access token for authenticated API calls."""
    client = AuthClient(config)
    try:
        response = client.login("admin@eqe.com", "Admin@123")
        if response.status_code == 200:
            token = response.json().get("access_token")
            logger.info("Session JWT authentication token obtained successfully.")
            return token
    except Exception as e:
        logger.warning(f"Could not authenticate online API session ({e}). Returning fallback token.")
    return "mock-jwt-token"


@pytest.fixture(scope="session")
def db_client(config: Config) -> DatabaseClient:
    return DatabaseClient(config)


# ── Failure Artifact Capture ──────────────────────────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook: captures rich failure artifacts when a UI test fails.

    Artifacts saved per failing test:
      1. Screenshot (.png)
      2. Browser console logs (.json)
      3. HTML page source snapshot (.html)
      4. Failure metadata (.json): test name, URL, timestamp, error message
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver_fixture = item.funcargs.get("driver")
        if not driver_fixture:
            return  # Non-UI test — no browser artifacts to capture

        ts = int(time.time())
        safe_name = item.name.replace("[", "_").replace("]", "_").replace(" ", "_")
        prefix = f"FAIL_{safe_name}_{ts}"

        artifacts_captured = {}

        # 1. Screenshot
        try:
            ss_path = os.path.join(_SCREENSHOTS_DIR, f"{prefix}.png")
            driver_fixture.save_screenshot(ss_path)
            artifacts_captured["screenshot"] = ss_path
            logger.error(f"[FailureCapture] Screenshot: {ss_path}")
        except Exception as e:
            logger.error(f"[FailureCapture] Screenshot failed: {e}")

        # 2. Browser console logs
        try:
            console_logs = driver_fixture.get_log("browser")
            logs_path = os.path.join(_ARTIFACTS_DIR, f"{prefix}_console.json")
            with open(logs_path, "w", encoding="utf-8") as f:
                json.dump(console_logs, f, indent=2, default=str)
            artifacts_captured["console_logs"] = logs_path
            if console_logs:
                errors = [e for e in console_logs if e.get("level") in ("SEVERE", "WARNING")]
                logger.error(f"[FailureCapture] {len(errors)} browser console error(s) captured.")
        except Exception as e:
            logger.warning(f"[FailureCapture] Console log capture failed: {e}")

        # 3. HTML page source snapshot
        try:
            src_path = os.path.join(_ARTIFACTS_DIR, f"{prefix}_page.html")
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(driver_fixture.page_source)
            artifacts_captured["page_source"] = src_path
        except Exception as e:
            logger.warning(f"[FailureCapture] Page source capture failed: {e}")

        # 4. Failure metadata JSON
        try:
            error_msg = str(report.longrepr)[:2000] if report.longrepr else "Unknown"
            metadata = {
                "test_name": item.name,
                "test_file": str(item.fspath),
                "url_at_failure": driver_fixture.current_url,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
                "error_message": error_msg,
                "browser": "Chrome",
                "environment": item.funcargs.get("config", {}) and getattr(
                    item.funcargs.get("config"), "env_name", "local"
                ),
                "artifacts": artifacts_captured
            }
            meta_path = os.path.join(_ARTIFACTS_DIR, f"{prefix}_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            logger.error(f"[FailureCapture] Failure metadata: {meta_path}")
        except Exception as e:
            logger.warning(f"[FailureCapture] Metadata capture failed: {e}")

        # Attach screenshot to pytest-html report if available
        try:
            if "screenshot" in artifacts_captured:
                extras = getattr(report, "extras", [])
                from pytest_html import extras as html_extras
                extras.append(html_extras.image(artifacts_captured["screenshot"]))
                report.extras = extras
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"[FailureCapture] pytest-html extra attachment failed: {e}")


# ── Session Finish — Dashboard Generation ─────────────────────────────────────
def pytest_sessionfinish(session, exitstatus):
    """After the test run, generate the quality dashboard HTML."""
    try:
        from reports.dashboard.generate_dashboard import generate
        generate()
        logger.info("Quality dashboard generated: reports/dashboard/index.html")
    except Exception as e:
        logger.warning(f"Dashboard generation skipped: {e}")
