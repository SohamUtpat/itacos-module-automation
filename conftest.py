import base64
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page

from pages.login_page import LoginPage

load_dotenv()

REPORTS_DIR = Path("reports")
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"


def pytest_configure(config):
    REPORTS_DIR.mkdir(exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def login_page(page: Page):
    base_url = os.getenv("BASE_URL")

    if not base_url:
        pytest.fail("BASE_URL is missing in .env")

    page.goto(base_url)

    yield page

    logout = page.get_by_role("button", name="Logout")
    if logout.is_visible():
        logout.click()


@pytest.fixture
def authenticated_page(page: Page):
    """Login as Provider Office Admin and land on the dashboard."""
    base_url = os.getenv("BASE_URL")
    email = os.getenv("LOGIN_EMAIL_OR_MOBILE")
    password = os.getenv("LOGIN_PASSWORD")

    if not base_url:
        pytest.fail("BASE_URL is missing in .env")
    if not email or not password:
        pytest.fail("LOGIN_EMAIL_OR_MOBILE and LOGIN_PASSWORD must be set in .env")

    page.goto(base_url)
    LoginPage(page).login(email, password)
    page.get_by_role("button", name="Provider Office Admin").wait_for(
        state="visible", timeout=20_000
    )

    yield page

    logout = page.get_by_role("button", name="Logout")
    if logout.is_visible():
        logout.click()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """On failure: save a screenshot and attach it to the pytest-html report."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    page = _page_from_item(item)
    if page is None:
        return

    safe_name = item.nodeid.replace("/", "_").replace("\\", "_").replace("::", "_")
    screenshot_path = SCREENSHOTS_DIR / f"{safe_name}.png"

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception as exc:  # noqa: BLE001 — never fail the hook
        report.sections.append(("Screenshot error", str(exc)))
        return

    # Attach PNG bytes so the self-contained HTML report embeds the image
    extras = getattr(report, "extras", [])
    try:
        from pytest_html import extras as html_extras

        encoded = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
        extras.append(html_extras.png(encoded))
        report.sections.append(("Screenshot file", str(screenshot_path.resolve())))
    except Exception as exc:  # noqa: BLE001
        report.sections.append(("Screenshot", f"{screenshot_path} ({exc})"))
    report.extras = extras


def _page_from_item(item):
    for name in ("authenticated_page", "login_page", "page"):
        if name in item.funcargs:
            return item.funcargs[name]
    return None
