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


@pytest.fixture(scope="module")
def _login_browser_page(_module_context):
    """One login window for the whole file. Closed after that file's last case."""
    page = _module_context.new_page()
    yield page
    if not page.is_closed():
        page.close()


@pytest.fixture
def login_page(_login_browser_page: Page):
    """Reload a logged-out login form in the shared window before each case.

    A successful case leaves a session in this window. Reload alone would open
    the signed-in app, so sign out first, then load the login address again.
    That clears the fields and any error toast without closing the window.
    """
    base_url = os.getenv("BASE_URL")

    if not base_url:
        pytest.fail("BASE_URL is missing in .env")

    _prepare_login_form(_login_browser_page, base_url)
    yield _login_browser_page


def _prepare_login_form(page: Page, base_url: str) -> None:
    if page.is_closed():
        pytest.fail("Shared login page was closed by an earlier test in this module")

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    logout = page.get_by_role("button", name="Logout")
    if logout.is_visible():
        logout.click()
        # Logout asks for confirmation and stays on the signed-in page until Confirm.
        page.get_by_role("button", name="Confirm").click()
        page.get_by_role("heading", name="Welcome Back").wait_for(
            state="visible", timeout=20_000
        )

    page.goto(base_url, wait_until="domcontentloaded")
    page.get_by_role("heading", name="Welcome Back").wait_for(
        state="visible", timeout=20_000
    )


# Post-login URL for the module-scoped page, so later tests can reload the
# shell without sending the browser back through the login form.
_session_home_urls: dict[int, str] = {}


@pytest.fixture(scope="module")
def _module_context(browser, browser_context_args):
    """One browser context per test file, shared by the login window and the signed-in page."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="module")
def authenticated_page(_module_context):
    """Log in once per test file and log out after that file's last test."""
    base_url = os.getenv("BASE_URL")
    email = os.getenv("LOGIN_EMAIL_OR_MOBILE")
    password = os.getenv("LOGIN_PASSWORD")

    if not base_url:
        pytest.fail("BASE_URL is missing in .env")
    if not email or not password:
        pytest.fail("LOGIN_EMAIL_OR_MOBILE and LOGIN_PASSWORD must be set in .env")

    page = _module_context.new_page()
    page.goto(base_url)
    LoginPage(page).login(email, password)
    page.get_by_role("button", name="Provider Office Admin").wait_for(
        state="visible", timeout=20_000
    )
    _session_home_urls[id(page)] = page.url

    yield page

    try:
        if page.is_closed():
            return
        home_url = _session_home_urls.get(id(page))
        if home_url:
            page.goto(home_url, wait_until="domcontentloaded")
        logout = page.get_by_role("button", name="Logout")
        if logout.is_visible():
            logout.click()
    finally:
        _session_home_urls.pop(id(page), None)
        if not page.is_closed():
            page.close()


@pytest.fixture(autouse=True)
def _reset_shared_session(request):
    """Reload the post-login shell before each authenticated test.

    The page is shared for the whole file, so search text, map view, open
    dialogs, and unsaved form values would otherwise leak into the next test.
    Login cases use login_page, which reloads the login form in its own window.
    """
    if "authenticated_page" not in request.fixturenames:
        yield
        return

    page = request.getfixturevalue("authenticated_page")
    _prepare_shared_page(page)
    yield


def _prepare_shared_page(page: Page) -> None:
    if page.is_closed():
        pytest.fail("Shared browser page was closed by an earlier test in this module")

    home_url = _session_home_urls.get(id(page))
    if not home_url:
        return

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    page.goto(home_url, wait_until="domcontentloaded")
    page.get_by_role("button", name="Provider Office Admin").wait_for(
        state="visible", timeout=20_000
    )


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
