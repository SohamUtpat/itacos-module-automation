"""Login API tests for POST /user-management-service/v1/login.

UI-only checks such as password masking and button labels stay in tests/test_login.py.
Negative cases assert HTTP status plus error messages returned in the live API response.
"""

import json
from pathlib import Path

import pytest

from api.endpoints.auth_endpoints import LOGIN_PATH, build_login_payload
from api.helpers.checks import (
    assert_password_absent,
    assert_rejected,
    require_text,
    safe_error_summary,
    value_at,
)

API_DIR = Path(__file__).resolve().parents[1]
LOGIN_DATA = json.loads((API_DIR / "test_data" / "login_data.json").read_text(encoding="utf-8"))
LOGIN_SCHEMA = json.loads(
    (API_DIR / "schemas" / "login_response_schema.json").read_text(encoding="utf-8")
)

USER_PATH = "data.loginAudit.userBasicDetails"

pytestmark = pytest.mark.api


def _credentials(api_config):
    if not api_config["username"] or not api_config["password"]:
        pytest.fail("Set API_USERNAME and API_PASSWORD in .env")
    return api_config["username"], api_config["password"]


def _case_payload(case, username, password):
    user_name = case.get("user_name", "ENV")
    case_password = case.get("password", "ENV")

    if user_name == "ENV":
        user_name = username
    elif user_name == "SPACES":
        user_name = f"  {username}  "

    if case_password == "ENV":
        case_password = password
    elif case_password == "CASE":
        if not password or password.swapcase() == password:
            pytest.skip("Password has no letter-case difference to test")
        case_password = password.swapcase()

    payload = build_login_payload(
        user_name,
        case_password,
        app_type=case.get("app_type", "WEB"),
        force_login=case.get("force_login", True),
        include_user_name=case.get("include_user_name", True),
        include_password=case.get("include_password", True),
    )
    return payload, case_password


def _permission_names(body):
    permissions = value_at(body, f"{USER_PATH}.permission")
    if not isinstance(permissions, list):
        pytest.fail("Login response did not include a permission list")
    names = []
    for item in permissions:
        if isinstance(item, dict) and isinstance(item.get("permission"), str):
            names.append(item["permission"])
    return names


def _contains_key(value, key):
    if isinstance(value, dict):
        if key in value:
            return True
        return any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def _department_names(body):
    assignments = value_at(body, f"{USER_PATH}.userRolesPostResponse")
    if not isinstance(assignments, list):
        pytest.fail("Login response did not include userRolesPostResponse")
    names = []
    for item in assignments:
        if isinstance(item, dict) and isinstance(item.get("departmentName"), str):
            names.append(item["departmentName"])
    return names


@pytest.mark.smoke
def test_login_with_valid_username_and_password(valid_login):
    if valid_login["status"] != 201:
        pytest.fail(
            "Valid credentials were rejected. "
            f"HTTP {valid_login['status']}. Details: {safe_error_summary(valid_login['body'])}"
        )
    message = valid_login["body"].get("message")
    if message != LOGIN_DATA["success_message"]:
        pytest.fail(f"Unexpected login message: {message}")


@pytest.mark.smoke
def test_login_status_is_201(valid_login):
    if valid_login["status"] != 201:
        pytest.fail(f"Expected HTTP 201, got {valid_login['status']}")


@pytest.mark.smoke
def test_login_success_message(valid_login):
    message = valid_login["body"].get("message")
    if message != LOGIN_DATA["success_message"]:
        pytest.fail(f"Expected '{LOGIN_DATA['success_message']}', got '{message}'")


@pytest.mark.smoke
def test_login_returns_a_token(valid_login):
    require_text(valid_login["body"], "data.loginAudit.token", "a token")


@pytest.mark.regression
def test_login_returns_user_id(valid_login):
    require_text(valid_login["body"], f"{USER_PATH}.id", "a user id")


@pytest.mark.regression
def test_login_returns_tenant_id(valid_login):
    require_text(valid_login["body"], f"{USER_PATH}.tenantId", "a tenant id")


@pytest.mark.regression
def test_login_returns_first_and_last_name(valid_login):
    require_text(valid_login["body"], f"{USER_PATH}.firstName", "a first name")
    require_text(valid_login["body"], f"{USER_PATH}.lastName", "a last name")


@pytest.mark.regression
def test_login_user_type_is_service_provider(valid_login):
    actual = value_at(valid_login["body"], f"{USER_PATH}.userType")
    expected = LOGIN_DATA["account"]["user_type"]
    if actual != expected:
        pytest.fail(f"Expected user type '{expected}', got '{actual}'")


@pytest.mark.regression
def test_login_role_is_provider_office_admin(valid_login):
    actual = value_at(valid_login["body"], f"{USER_PATH}.role.role")
    expected = LOGIN_DATA["account"]["role"]
    if actual != expected:
        pytest.fail(f"Expected role '{expected}', got '{actual}'")


@pytest.mark.regression
def test_login_department_is_service_providers(valid_login):
    expected = LOGIN_DATA["account"]["department"]
    departments = _department_names(valid_login["body"])
    if expected not in departments:
        pytest.fail(f"Expected department '{expected}', got {departments}")


@pytest.mark.regression
def test_login_permissions_for_provider_office_admin(valid_login):
    expected = sorted(LOGIN_DATA["account"]["permissions"])
    actual = sorted(_permission_names(valid_login["body"]))
    if actual != expected:
        pytest.fail(
            "Permissions for this Provider Office Admin account did not match. "
            f"Expected {expected}, got {actual}"
        )


@pytest.mark.regression
def test_login_response_matches_schema(valid_login):
    body = valid_login["body"]
    missing = [path for path in LOGIN_SCHEMA["required_paths"] if value_at(body, path) is None]
    if missing:
        pytest.fail(f"Login response is missing: {', '.join(missing)}")


@pytest.mark.regression
def test_login_content_type_is_json(valid_login):
    content_type = valid_login["content_type"]
    if "application/json" not in content_type:
        pytest.fail(f"Expected application/json, got '{content_type}'")


@pytest.mark.regression
def test_login_response_time_within_threshold(valid_login, api_config):
    limit = api_config["max_response_ms"]
    elapsed = valid_login["elapsed_ms"]
    if elapsed > limit:
        pytest.fail(f"Login took {elapsed:.0f} ms, which is over the {limit} ms limit")


@pytest.mark.regression
def test_login_with_username_case_variation(api_client, api_config):
    """Same business rule as UI TC-L12: email letter case still logs in."""
    username, password = _credentials(api_config)
    if username.swapcase() == username:
        pytest.skip("Username has no letter-case difference to test")

    response = api_client.post(
        LOGIN_PATH,
        build_login_payload(username.swapcase(), password),
    )
    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Login response was not JSON (HTTP {response.status})")

    if response.status != 201 or body.get("message") != LOGIN_DATA["success_message"]:
        pytest.fail(
            f"Username case variation was rejected (HTTP {response.status}). "
            f"Details: {safe_error_summary(body)}"
        )
    require_text(body, "data.loginAudit.token", "a token")
    assert_password_absent(body, password)


@pytest.mark.regression
def test_login_with_valid_mobile(api_client, api_config):
    """Same business rule as UI TC-L02."""
    if not api_config["mobile"] or not api_config["password"]:
        pytest.skip("Set API_MOBILE or LOGIN_MOBILE, and a password, to run mobile login")

    response = api_client.post(
        LOGIN_PATH,
        build_login_payload(api_config["mobile"], api_config["password"]),
    )
    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Login response was not JSON (HTTP {response.status})")

    if response.status != 201 or body.get("message") != LOGIN_DATA["success_message"]:
        pytest.fail(
            f"Mobile login was rejected (HTTP {response.status}). "
            f"Details: {safe_error_summary(body)}"
        )
    require_text(body, "data.loginAudit.token", "a token")
    assert_password_absent(body, api_config["password"])


@pytest.mark.regression
@pytest.mark.parametrize("case", LOGIN_DATA["negative_cases"], ids=lambda case: case["id"])
def test_login_rejects_invalid_request(api_client, api_config, case):
    username, password = _credentials(api_config)
    payload, sent_password = _case_payload(case, username, password)
    response = api_client.post(LOGIN_PATH, payload)
    assert_rejected(response, sent_password, case["expected_status"])


@pytest.mark.regression
def test_password_is_never_returned(valid_login, api_config):
    assert_password_absent(valid_login["body"], api_config["password"])
    if _contains_key(valid_login["body"], "password"):
        pytest.fail("Login response contains a password field")


@pytest.mark.regression
def test_sql_like_username_is_rejected(api_client):
    response = api_client.post(LOGIN_PATH, build_login_payload("' OR '1'='1", "test"))
    assert_rejected(response, "test", 404)


@pytest.mark.regression
def test_script_like_username_is_rejected(api_client):
    username = "<script>alert(1)</script>"
    response = api_client.post(LOGIN_PATH, build_login_payload(username, "test"))
    assert_rejected(response, "test", 404)
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        pytest.fail("Script-like username was returned as HTML")


@pytest.mark.regression
def test_repeated_invalid_logins_stay_rejected(api_client):
    """UAT currently returns 404 for each of five bad attempts and does not send 429.

    This uses a username that is not the real account. Update the expected
    status if a published rate limit starts returning HTTP 429.
    """
    payload = build_login_payload("rate.limit.probe@example.com", "WrongPassword123")
    for _attempt in range(5):
        response = api_client.post(LOGIN_PATH, payload)
        assert_rejected(response, "WrongPassword123", 404)


@pytest.mark.smoke
def test_authenticated_client_has_bearer_header(authenticated_api):
    header = authenticated_api.default_headers.get("Authorization", "")
    if not header.startswith("Bearer ") or len(header) <= len("Bearer "):
        pytest.fail("Authenticated client is missing a Bearer authorization header")
