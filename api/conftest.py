"""Fixtures for Itacos API tests.

Login runs once per pytest session. Negative login tests use api_client
and do not depend on this token, so a failed login does not skip them.
The token is kept in memory and is not printed.

Protected unit/admin calls also need x-tenant-id (and user-id for
provider-office). Those headers are set on authenticated_api.
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from api.clients.api_client import ApiClient
from api.endpoints.auth_endpoints import LOGIN_PATH, build_login_payload
from api.endpoints.unit_endpoints import (
    PROVIDER_OFFICE_PATH,
    branches_path,
    delete_unit_path,
)
from api.helpers.checks import assert_password_absent, value_at

load_dotenv()

API_DIR = Path(__file__).resolve().parent
UNIT_DATA = json.loads((API_DIR / "test_data" / "unit_data.json").read_text(encoding="utf-8"))


def _setting(*names):
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _base_url():
    configured = _setting("API_BASE_URL")
    if configured:
        return configured.rstrip("/")

    parsed = urlparse(os.getenv("BASE_URL", ""))
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"

    pytest.fail("Set API_BASE_URL in .env (example: https://uat.assistme.me)")


@pytest.fixture(scope="session")
def api_config():
    return {
        "base_url": _base_url(),
        "username": _setting("API_USERNAME", "LOGIN_EMAIL_OR_MOBILE"),
        "password": _setting("API_PASSWORD", "LOGIN_PASSWORD"),
        "mobile": _setting("API_MOBILE", "LOGIN_MOBILE"),
        "max_response_ms": int(os.getenv("API_MAX_RESPONSE_MS", "5000")),
        "branch_code": _setting("API_BRANCH_CODE")
        or UNIT_DATA["default_branch_code"],
        "unit_password": _setting("API_UNIT_PASSWORD") or UNIT_DATA["password"],
    }


@pytest.fixture(scope="session")
def _playwright_instance():
    instance = sync_playwright().start()
    yield instance
    instance.stop()


@pytest.fixture(scope="session")
def api_client(_playwright_instance, api_config):
    """Unauthenticated client. Used by negative login tests."""
    context = _playwright_instance.request.new_context(base_url=api_config["base_url"])
    yield ApiClient(context)
    context.dispose()


def _require_credentials(api_config):
    if not api_config["username"] or not api_config["password"]:
        pytest.fail("Set API_USERNAME and API_PASSWORD in .env")


@pytest.fixture(scope="session")
def valid_login(api_client, api_config):
    """One successful login shared by the positive checks."""
    _require_credentials(api_config)
    payload = build_login_payload(api_config["username"], api_config["password"])
    started = time.perf_counter()
    response = api_client.post(LOGIN_PATH, payload)
    elapsed_ms = (time.perf_counter() - started) * 1000

    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Login response was not JSON (HTTP {response.status})")

    assert_password_absent(body, api_config["password"])
    return {
        "status": response.status,
        "content_type": response.headers.get("content-type", ""),
        "body": body,
        "elapsed_ms": elapsed_ms,
    }


@pytest.fixture(scope="session")
def auth_token(valid_login):
    token = value_at(valid_login["body"], "data.loginAudit.token")
    if not isinstance(token, str) or not token.strip():
        pytest.fail("Successful login did not return a token at data.loginAudit.token")
    return token


@pytest.fixture(scope="session")
def tenant_id(valid_login):
    value = value_at(valid_login["body"], "data.loginAudit.userBasicDetails.tenantId")
    if not isinstance(value, str) or not value.strip():
        pytest.fail("Login response did not include tenantId")
    return value


@pytest.fixture(scope="session")
def auth_user_id(valid_login):
    value = value_at(valid_login["body"], "data.loginAudit.userBasicDetails.id")
    if not isinstance(value, str) or not value.strip():
        pytest.fail("Login response did not include user id")
    return value


@pytest.fixture(scope="session")
def authenticated_api(
    _playwright_instance, api_config, auth_token, tenant_id, auth_user_id
):
    """Client that sends Bearer + tenant/user headers on later requests.

    Session scope matches a short suite: the token is created once and
    discarded when the run ends. Start a new run if the token expires.

    x-tenant-id is required by admin-service unit/branch endpoints.
    user-id is required by GET /admin-service/v1/provider-office.
    """
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "x-tenant-id": tenant_id,
        "user-id": auth_user_id,
        "Accept": "application/json, text/plain, */*",
    }
    context = _playwright_instance.request.new_context(
        base_url=api_config["base_url"],
        extra_http_headers=headers,
    )
    yield ApiClient(context, default_headers=headers)
    context.dispose()


@pytest.fixture(scope="session")
def provider_id(authenticated_api):
    response = authenticated_api.get(PROVIDER_OFFICE_PATH)
    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Provider office response was not JSON (HTTP {response.status})")

    if response.status != 200:
        pytest.fail(
            f"Could not load provider office (HTTP {response.status}). "
            "Unit API tests need an office for this Provider Office Admin."
        )

    value = value_at(body, "data.providerOffice.id")
    if not isinstance(value, str) or not value.strip():
        pytest.fail("Provider office response did not include data.providerOffice.id")
    return value


@pytest.fixture(scope="session")
def default_branch(authenticated_api, api_config, provider_id):
    """Resolve the configured branch code to its id (default SP-B008)."""
    response = authenticated_api.get(branches_path(provider_id))
    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Branches response was not JSON (HTTP {response.status})")

    if response.status != 200:
        pytest.fail(f"Could not load branches (HTTP {response.status})")

    branches = value_at(body, "data.providerBranch")
    if not isinstance(branches, list) or not branches:
        pytest.fail("No branches found for this provider office")

    code = api_config["branch_code"]
    match = next((item for item in branches if item.get("code") == code), None)
    if match is None:
        available = [item.get("code") for item in branches[:8]]
        pytest.fail(
            f"Branch code '{code}' was not found. "
            f"Set API_BRANCH_CODE. Sample codes: {available}"
        )
    return {"id": match["id"], "code": match["code"]}


@pytest.fixture(scope="session")
def created_unit_ids():
    """Track unit ids created during the session so they can be deactivated."""
    return []


@pytest.fixture(scope="session", autouse=True)
def _cleanup_created_units(created_unit_ids, authenticated_api):
    yield
    for unit_id in list(created_unit_ids):
        try:
            authenticated_api.delete(delete_unit_path(unit_id))
        except Exception:
            pass
