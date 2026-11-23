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
    """Return non-empty errorMessage values from the API response body."""
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(errors, list):
        return []
    messages = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        message = item.get("errorMessage")
        if isinstance(message, str) and message.strip():
            messages.append(message)
    return messages


def response_error_text(body):
    """Return the top-level error string from the API response, if present."""
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    if isinstance(error, str) and error.strip():
        return error
    return None


def safe_error_summary(body):
    """Details that are safe to show when a status code does not match."""
    if not isinstance(body, dict):
        return "response was not a JSON object"
    messages = error_messages(body)
    if messages:
        return messages
    error = response_error_text(body)
    if error:
        return {"status": body.get("status"), "error": error}
    return {"keys": sorted(body.keys())}


def assert_rejected(response, password, expected_status):
    """Assert a rejected login using HTTP status and error details from the API response."""
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

    actual_messages = error_messages(body)
    actual_error = response_error_text(body)
    if not actual_messages and not actual_error:
        pytest.fail(
            "Rejected login API response did not include error messages "
            "(expected errors[].errorMessage or a top-level error field)"
        )

    return body
