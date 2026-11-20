"""Fixtures for Itacos API tests.

Login runs once per pytest session. Negative login tests use api_client
and do not depend on this token, so a failed login does not skip them.
The token is kept in memory and is not printed.
"""

import os
import time
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from api.clients.api_client import ApiClient
from api.endpoints.auth_endpoints import LOGIN_PATH, build_login_payload
from api.helpers.checks import assert_password_absent, value_at

load_dotenv()


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
def authenticated_api(_playwright_instance, api_config, auth_token):
    """Client that sends Authorization: Bearer <token> on later requests.

    Session scope matches a short suite: the token is created once and
    discarded when the run ends. Start a new run if the token expires.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    context = _playwright_instance.request.new_context(
        base_url=api_config["base_url"],
        extra_http_headers=headers,
    )
    yield ApiClient(context, default_headers=headers)
    context.dispose()
