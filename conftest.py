import base64
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page

from pages.login_page import LoginPage

load_dotenv()

REPORTS_DIR = Path("reports")
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"

# List URL for each UI test file (CRUD soft-reset target).
_TEST_FILE_MODULE_PATHS = {
    "test_units.py": "/service-provider/units",
    "test_branches.py": "/service-provider/branches",
    "test_workshops.py": "/service-provider/garages",
    "test_office.py": "/service-provider/provider-office/manage-office",
    "test_office_branch_unit_e2e.py": "/service-provider/provider-office/manage-office",
}

# Create/form URL for negative hard-reset (reload in place between rejection cases).
_TEST_FILE_CREATE_PATHS = {
    "test_units.py": "/service-provider/units/create",
    "test_branches.py": "/service-provider/branches/create",
    "test_workshops.py": "/service-provider/garages/create",
    "test_office.py": "/service-provider/provider-office/manage-office",
}

# Map deep links (create / edit) back to that module's list page.
_MODULE_PATH_PREFIXES = (
    ("/service-provider/users/update", "/service-provider/units"),
    ("/service-provider/units", "/service-provider/units"),
    ("/service-provider/branches", "/service-provider/branches"),
    ("/service-provider/garages", "/service-provider/garages"),
    (
        "/service-provider/provider-office",
        "/service-provider/provider-office/manage-office",
    ),
)


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


# Post-login URL used only for logout teardown (dashboard is fine there).
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
        # Log out from whatever module page the last test left open (Units,
        # Branches, …) — do not bounce to the dashboard first.
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        logout = page.get_by_role("button", name="Logout")
        if logout.is_visible():
            logout.click()
            confirm = page.get_by_role("button", name="Confirm")
            if confirm.is_visible():
                confirm.click()
    finally:
        _session_home_urls.pop(id(page), None)
        if not page.is_closed():
            page.close()


@pytest.fixture(autouse=True)
def _reset_shared_session(request):
    """Prepare the shared browser before each authenticated test.

    Negative cases stay on (or open) the create form and reload it in place so
    the next rejection case does not bounce through the list. CRUD / positive
    cases stay on the list when already there. Login cases use login_page.
    """
    if "authenticated_page" not in request.fixturenames:
        yield
        return

    page = request.getfixturevalue("authenticated_page")
    _prepare_shared_page(page, request)
    yield


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def _normalize_path(url: str) -> str:
    return (urlparse(url).path or "").rstrip("/")


def _test_file_name(request) -> str | None:
    path = getattr(request, "path", None) or getattr(request.node, "fspath", None)
    if path is None:
        return None
    return Path(str(path)).name


def _module_list_url_from_path(page_url: str) -> str | None:
    """If the browser is on a known module route, return that module's list URL."""
    parsed = urlparse(page_url)
    path = (parsed.path or "").rstrip("/")
    if not path:
        return None

    for prefix, list_path in _MODULE_PATH_PREFIXES:
        if path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/"):
            return urlunparse((parsed.scheme, parsed.netloc, list_path, "", "", ""))
    return None


def _module_list_url_for_test(request, origin: str) -> str | None:
    """List URL for the current test file (e.g. test_units.py → /units)."""
    name = _test_file_name(request)
    if not name:
        return None
    module_path = _TEST_FILE_MODULE_PATHS.get(name)
    if not module_path:
        return None
    return f"{origin.rstrip('/')}{module_path}"


def _create_url_for_test(request, origin: str) -> str | None:
    """Create/form URL for the current test file (e.g. …/units/create)."""
    name = _test_file_name(request)
    if not name:
        return None
    create_path = _TEST_FILE_CREATE_PATHS.get(name)
    if not create_path:
        return None
    return f"{origin.rstrip('/')}{create_path}"


def _resolve_module_list_url(page: Page, request, home_url: str) -> str:
    origin = _origin_from_url(home_url) or _origin_from_url(page.url or "")
    current = (page.url or "").strip()

    target = None
    if current and not current.startswith("about:"):
        target = _module_list_url_from_path(current)
    if not target and origin:
        target = _module_list_url_for_test(request, origin)
    return target or home_url


def _is_on_module_list(page_url: str, list_url: str) -> bool:
    """True only on the module list itself — not create/edit/dashboard."""
    return _normalize_path(page_url) == _normalize_path(list_url)


def _prepare_shared_page(page: Page, request) -> None:
    if page.is_closed():
        pytest.fail("Shared browser page was closed by an earlier test in this module")

    home_url = _session_home_urls.get(id(page))
    if not home_url:
        return

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    origin = _origin_from_url(home_url) or _origin_from_url(page.url or "")
    hard_reset = request.node.get_closest_marker("negative") is not None

    create_url = _create_url_for_test(request, origin) if origin else None

    if hard_reset:
        # Stay on create: reload in place. First negative opens create directly.
        # Same for Office (form-only module — create URL == manage-office).
        if create_url and _normalize_path(page.url or "") == _normalize_path(create_url):
            page.reload(wait_until="domcontentloaded")
        elif create_url:
            page.goto(create_url, wait_until="domcontentloaded")
        else:
            page.goto(
                _resolve_module_list_url(page, request, home_url),
                wait_until="domcontentloaded",
            )
    else:
        # CRUD: stay on the list when already there; otherwise land on the list.
        # Form-only modules (Office) reload so negative validation cannot leak.
        list_url = _resolve_module_list_url(page, request, home_url)
        if not _is_on_module_list(page.url or "", list_url):
            page.goto(list_url, wait_until="domcontentloaded")
        elif create_url and _normalize_path(create_url) == _normalize_path(list_url):
            page.reload(wait_until="domcontentloaded")

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
