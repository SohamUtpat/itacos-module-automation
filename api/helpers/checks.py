"""Small checks for login responses.

Failure messages intentionally omit tokens, passwords, and personal fields.
"""

import json

import pytest

_LEAK_MARKERS = (
    "traceback",
    "stacktrace",
    "sql syntax",
    "sqlexception",
    "java.lang",
)


def value_at(body, path):
    current = body
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def require_text(body, path, label):
    value = value_at(body, path)
    if not isinstance(value, str) or not value.strip():
        pytest.fail(f"Login response did not include {label}")
    return value


def assert_password_absent(body, password):
    if password and password in json.dumps(body):
        pytest.fail("Password was included in the API response")


def assert_no_token(body):
    token = value_at(body, "data.loginAudit.token")
    if token:
        pytest.fail("A login token was returned for a rejected login")


def assert_no_server_leak(body):
    text = json.dumps(body).lower()
    for marker in _LEAK_MARKERS:
        if marker in text:
            pytest.fail("Error response exposed server or database details")


def error_messages(body):
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(errors, list):
        return []
    return [item.get("errorMessage") for item in errors if isinstance(item, dict)]


def safe_error_summary(body):
    """Details that are safe to show when a status code does not match."""
    if not isinstance(body, dict):
        return "response was not a JSON object"
    if "errors" in body:
        return error_messages(body)
    if "error" in body:
        return {"status": body.get("status"), "error": body.get("error")}
    return {"keys": sorted(body.keys())}


def assert_rejected(response, password, expected_status, expected_messages=None, expected_error=None):
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        pytest.fail(f"Expected a JSON response, got content-type '{content_type}'")

    try:
        body = response.json()
    except Exception:
        pytest.fail(f"Rejected login did not return JSON (HTTP {response.status})")

    if response.status != expected_status:
        pytest.fail(
            f"Expected HTTP {expected_status}, got {response.status}. "
            f"Details: {safe_error_summary(body)}"
        )

    assert_no_token(body)
    assert_password_absent(body, password)
    assert_no_server_leak(body)

    if expected_messages is not None and error_messages(body) != expected_messages:
        pytest.fail(f"Unexpected error messages: {error_messages(body)}")

    if expected_error is not None and body.get("error") != expected_error:
        pytest.fail(f"Unexpected error value: {body.get('error')}")

    return body
