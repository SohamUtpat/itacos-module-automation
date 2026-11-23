"""Units API tests for ITACO Service Provider Unit CRUD.

UI-only checks such as Map view, Reset, and dialog Cancel stay in tests/test_units.py.
Endpoints and messages come from the current UAT Network tab.
"""

import json
import itertools
import time
from pathlib import Path

import pytest

from api.endpoints.unit_endpoints import (
    CREATE_UNIT_PATH,
    build_create_unit_payload,
    build_update_unit_payload,
    delete_unit_path,
    list_units_path,
    update_unit_path,
)
from api.helpers.checks import (
    assert_error_status,
    assert_password_absent,
    parse_json,
    require_text,
    safe_error_summary,
    value_at,
)
from helpers.unique import unique_first_name, unique_last_name

API_DIR = Path(__file__).resolve().parents[1]
UNIT_DATA = json.loads((API_DIR / "test_data" / "unit_data.json").read_text(encoding="utf-8"))
CREATE_SCHEMA = json.loads(
    (API_DIR / "schemas" / "unit_create_response_schema.json").read_text(encoding="utf-8")
)
LIST_SCHEMA = json.loads(
    (API_DIR / "schemas" / "unit_list_response_schema.json").read_text(encoding="utf-8")
)

USER_PATH = "data.itacoUserResponse.userBasicDetails"
_seq = itertools.count(1)

pytestmark = pytest.mark.api


def _unique_mobile() -> str:
    """10-digit mobile that stays unique inside the same second."""
    n = next(_seq)
    return f"9{str(int(time.time()))[-7:]}{n:02d}"[:10]


def _unique_unit_email(prefix: str = "api.unit") -> str:
    n = next(_seq)
    return f"{prefix}.{int(time.time())}.{n}@example.com"


def _new_unit_fields():
    return {
        "first_name": unique_first_name(),
        "last_name": unique_last_name(),
        "email": _unique_unit_email(),
        "phone": _unique_mobile(),
    }


def _create_payload(api_config, provider_id, default_branch, **overrides):
    fields = _new_unit_fields()
    fields.update(overrides)
    return build_create_unit_payload(
        first_name=fields["first_name"],
        last_name=fields.get("last_name", ""),
        email=fields["email"],
        phone=fields["phone"],
        password=api_config["unit_password"],
        provider_id=provider_id,
        branch_id=default_branch["id"],
        country_code=UNIT_DATA["country_code"],
        include_branch_id=fields.get("include_branch_id", True),
        include_password=fields.get("include_password", True),
    ), fields


def _create_unit(
    authenticated_api, api_config, provider_id, default_branch, created_unit_ids, **overrides
):
    payload, fields = _create_payload(
        api_config, provider_id, default_branch, **overrides
    )
    started = time.perf_counter()
    response = authenticated_api.post(CREATE_UNIT_PATH, payload)
    elapsed_ms = (time.perf_counter() - started) * 1000
    body = parse_json(response, "Create unit")
    if response.status == 201:
        unit_id = value_at(body, f"{USER_PATH}.id")
        if isinstance(unit_id, str) and unit_id:
            created_unit_ids.append(unit_id)
    return {
        "status": response.status,
        "content_type": response.headers.get("content-type", ""),
        "body": body,
        "elapsed_ms": elapsed_ms,
        "payload": payload,
        "fields": fields,
        "password": api_config["unit_password"],
    }


@pytest.fixture(scope="module")
def created_unit(
    authenticated_api, api_config, provider_id, default_branch, created_unit_ids
):
    """One successful create shared by the positive response checks.

    Matches the login suite pattern (valid_login): field assertions reuse a
    single response instead of creating a new unit per test.
    """
    result = _create_unit(
        authenticated_api,
        api_config,
        provider_id,
        default_branch,
        created_unit_ids,
    )
    if result["status"] != 201:
        pytest.fail(
            "Shared unit create failed. "
            f"HTTP {result['status']}. Details: {safe_error_summary(result['body'])}"
        )
    return result


# --- Create / response checks -------------------------------------------------


@pytest.mark.smoke
def test_create_unit_with_required_fields(created_unit):
    if created_unit["status"] != 201:
        pytest.fail(
            "Valid unit create was rejected. "
            f"HTTP {created_unit['status']}. Details: {safe_error_summary(created_unit['body'])}"
        )
    message = created_unit["body"].get("message")
    if message != UNIT_DATA["create_success_message"]:
        pytest.fail(f"Unexpected create message: {message}")


@pytest.mark.smoke
def test_create_unit_status_is_201(created_unit):
    if created_unit["status"] != 201:
        pytest.fail(f"Expected HTTP 201, got {created_unit['status']}")


@pytest.mark.smoke
def test_create_unit_success_message(created_unit):
    message = created_unit["body"].get("message")
    if message != UNIT_DATA["create_success_message"]:
        pytest.fail(
            f"Expected '{UNIT_DATA['create_success_message']}', got '{message}'"
        )


@pytest.mark.smoke
def test_create_unit_returns_id_and_code(created_unit):
    require_text(created_unit["body"], f"{USER_PATH}.id", "a unit user id")
    require_text(created_unit["body"], f"{USER_PATH}.unitCode", "a unit code")


@pytest.mark.regression
def test_create_unit_echoes_email_and_phone(created_unit):
    email = value_at(created_unit["body"], f"{USER_PATH}.email")
    phone = value_at(created_unit["body"], f"{USER_PATH}.phone")
    if email != created_unit["fields"]["email"]:
        pytest.fail("Create response email did not match the request")
    if phone != created_unit["fields"]["phone"]:
        pytest.fail("Create response phone did not match the request")


@pytest.mark.regression
def test_create_unit_role_and_department(created_unit):
    role = value_at(created_unit["body"], f"{USER_PATH}.role.role")
    department = value_at(created_unit["body"], f"{USER_PATH}.department.name")
    if role != UNIT_DATA["role"]:
        pytest.fail(f"Expected role '{UNIT_DATA['role']}', got '{role}'")
    if department != UNIT_DATA["department"]:
        pytest.fail(f"Expected department '{UNIT_DATA['department']}', got '{department}'")


@pytest.mark.regression
def test_create_unit_status_fields(created_unit):
    user_status = value_at(created_unit["body"], f"{USER_PATH}.userStatus")
    unit_status = value_at(created_unit["body"], f"{USER_PATH}.unitStatus")
    user_type = value_at(created_unit["body"], f"{USER_PATH}.userType")
    if user_status != UNIT_DATA["user_status"]:
        pytest.fail(f"Expected userStatus '{UNIT_DATA['user_status']}', got '{user_status}'")
    if unit_status != UNIT_DATA["unit_status"]:
        pytest.fail(f"Expected unitStatus '{UNIT_DATA['unit_status']}', got '{unit_status}'")
    if user_type != UNIT_DATA["user_type"]:
        pytest.fail(f"Expected userType '{UNIT_DATA['user_type']}', got '{user_type}'")


@pytest.mark.regression
def test_create_unit_links_selected_branch(created_unit, default_branch):
    branch_id = value_at(
        created_unit["body"], "data.itacoUserResponse.providerOfficeBranchResponse.id"
    )
    branch_code = value_at(
        created_unit["body"], "data.itacoUserResponse.providerOfficeBranchResponse.code"
    )
    if branch_id != default_branch["id"] or branch_code != default_branch["code"]:
        pytest.fail(
            f"Expected branch {default_branch}, got id={branch_id} code={branch_code}"
        )


@pytest.mark.regression
def test_create_unit_response_matches_schema(created_unit):
    missing = [
        path
        for path in CREATE_SCHEMA["required_paths"]
        if value_at(created_unit["body"], path) is None
    ]
    if missing:
        pytest.fail(f"Create response is missing: {', '.join(missing)}")


@pytest.mark.regression
def test_create_unit_content_type_is_json(created_unit):
    if "application/json" not in created_unit["content_type"]:
        pytest.fail(f"Expected application/json, got '{created_unit['content_type']}'")


@pytest.mark.regression
def test_create_unit_response_time_within_threshold(created_unit, api_config):
    limit = api_config["max_response_ms"]
    elapsed = created_unit["elapsed_ms"]
    if elapsed > limit:
        pytest.fail(f"Create unit took {elapsed:.0f} ms, which is over the {limit} ms limit")


@pytest.mark.regression
def test_create_unit_password_is_never_returned(created_unit):
    assert_password_absent(created_unit["body"], created_unit["password"])


# --- List / search ------------------------------------------------------------


@pytest.mark.smoke
def test_list_units_returns_success(authenticated_api):
    response = authenticated_api.get(list_units_path(page=1, size=20))
    body = parse_json(response, "List units")
    if response.status != 200:
        pytest.fail(
            f"List units failed (HTTP {response.status}). "
            f"Details: {safe_error_summary(body)}"
        )
    if body.get("message") != UNIT_DATA["list_success_message"]:
        pytest.fail(f"Unexpected list message: {body.get('message')}")
    users = value_at(body, "data.users")
    if not isinstance(users, list):
        pytest.fail("List response did not include data.users as a list")


@pytest.mark.regression
def test_list_units_response_matches_schema(authenticated_api):
    response = authenticated_api.get(list_units_path(page=1, size=5))
    body = parse_json(response, "List units")
    if response.status != 200:
        pytest.fail(f"List units failed (HTTP {response.status})")

    missing = [path for path in LIST_SCHEMA["required_paths"] if value_at(body, path) is None]
    if missing:
        pytest.fail(f"List response is missing: {', '.join(missing)}")

    users = value_at(body, "data.users") or []
    if not users:
        return

    item = users[0]
    item_missing = []
    for path in LIST_SCHEMA["item_required_paths"]:
        current = item
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                item_missing.append(path)
                break
            current = current[part]
    if item_missing:
        pytest.fail(f"List item is missing: {', '.join(item_missing)}")


@pytest.mark.regression
def test_search_units_by_email_finds_created_unit(authenticated_api, created_unit):
    email = created_unit["fields"]["email"]
    response = authenticated_api.get(list_units_path(search=email.split("@")[0]))
    body = parse_json(response, "Search units")
    if response.status != 200:
        pytest.fail(f"Search failed (HTTP {response.status})")

    users = value_at(body, "data.users") or []
    emails = [
        value_at(item, "userBasicDetails.email")
        for item in users
        if isinstance(item, dict)
    ]
    if email not in emails:
        pytest.fail(f"Created unit email was not returned by search. Got {emails[:5]}")


# --- Update / delete ----------------------------------------------------------


@pytest.mark.regression
def test_update_unit_first_name(authenticated_api, created_unit):
    unit_id = value_at(created_unit["body"], f"{USER_PATH}.id")
    response = authenticated_api.put(
        update_unit_path(unit_id),
        build_update_unit_payload(firstName="ApiEdited"),
    )
    body = parse_json(response, "Update unit")
    if response.status != 200:
        pytest.fail(
            f"Update failed (HTTP {response.status}). Details: {safe_error_summary(body)}"
        )
    if body.get("message") != UNIT_DATA["update_success_message"]:
        pytest.fail(f"Unexpected update message: {body.get('message')}")
    updated = value_at(body, f"{USER_PATH}.firstName")
    if updated != "ApiEdited":
        pytest.fail(f"Expected firstName 'ApiEdited', got '{updated}'")


@pytest.mark.regression
def test_update_unit_language_code(authenticated_api, created_unit):
    """Same business rule as UI Other Details language update (TC-U15)."""
    unit_id = value_at(created_unit["body"], f"{USER_PATH}.id")
    response = authenticated_api.put(
        update_unit_path(unit_id),
        build_update_unit_payload(languageCode="en"),
    )
    body = parse_json(response, "Update unit language")
    if response.status != 200:
        pytest.fail(
            f"Language update failed (HTTP {response.status}). "
            f"Details: {safe_error_summary(body)}"
        )
    if body.get("message") != UNIT_DATA["update_success_message"]:
        pytest.fail(f"Unexpected update message: {body.get('message')}")
    language = value_at(body, f"{USER_PATH}.languageCode")
    if language != "en":
        pytest.fail(f"Expected languageCode 'en', got '{language}'")


@pytest.mark.regression
def test_delete_unit_deactivates_row(authenticated_api, created_unit, created_unit_ids):
    unit_id = value_at(created_unit["body"], f"{USER_PATH}.id")
    response = authenticated_api.delete(delete_unit_path(unit_id))
    body = parse_json(response, "Delete unit")
    if response.status != 200:
        pytest.fail(
            f"Delete failed (HTTP {response.status}). Details: {safe_error_summary(body)}"
        )
    if body.get("message") != UNIT_DATA["delete_success_message"]:
        pytest.fail(f"Unexpected delete message: {body.get('message')}")
    if unit_id in created_unit_ids:
        created_unit_ids.remove(unit_id)


# --- Negative create ----------------------------------------------------------


@pytest.mark.regression
def test_create_unit_rejects_invalid_email(
    authenticated_api, api_config, provider_id, default_branch
):
    payload, _fields = _create_payload(
        api_config, provider_id, default_branch, email="not-an-email"
    )
    response = authenticated_api.post(CREATE_UNIT_PATH, payload)
    assert_error_status(
        response,
        400,
        password=api_config["unit_password"],
        message_contains=["Email is Invalid"],
    )


@pytest.mark.regression
def test_create_unit_rejects_alphabetic_phone(
    authenticated_api, api_config, provider_id, default_branch
):
    payload, _fields = _create_payload(
        api_config, provider_id, default_branch, phone="abcdefghij"
    )
    response = authenticated_api.post(CREATE_UNIT_PATH, payload)
    assert_error_status(
        response,
        400,
        password=api_config["unit_password"],
        message_contains=["invalid.phone.number"],
    )


@pytest.mark.regression
def test_create_unit_rejects_duplicate_email(
    authenticated_api, api_config, provider_id, default_branch, created_unit
):
    payload, _fields = _create_payload(
        api_config,
        provider_id,
        default_branch,
        email=created_unit["fields"]["email"],
    )
    response = authenticated_api.post(CREATE_UNIT_PATH, payload)
    assert_error_status(
        response,
        400,
        password=api_config["unit_password"],
        message_contains=["already exists"],
    )


@pytest.mark.regression
def test_create_unit_without_branch_id_still_succeeds_on_uat(
    authenticated_api, api_config, provider_id, default_branch, created_unit_ids
):
    """UI requires a branch (TC-U16). The create API currently accepts a body without branchId.

    Keep this assertion aligned with live UAT. Switch to a rejection check if
    the API starts enforcing branchId the same way as the form.
    """
    payload, _fields = _create_payload(
        api_config,
        provider_id,
        default_branch,
        include_branch_id=False,
    )
    response = authenticated_api.post(CREATE_UNIT_PATH, payload)
    body = parse_json(response, "Create without branch")
    assert_password_absent(body, api_config["unit_password"])
    if response.status != 201:
        pytest.fail(
            "UAT currently accepts create without branchId (HTTP 201). "
            f"Got HTTP {response.status}. Details: {safe_error_summary(body)}"
        )
    unit_id = value_at(body, f"{USER_PATH}.id")
    if isinstance(unit_id, str) and unit_id:
        created_unit_ids.append(unit_id)


@pytest.mark.regression
def test_create_unit_without_token_is_unauthorized(api_client, api_config, provider_id, default_branch):
    payload, _fields = _create_payload(api_config, provider_id, default_branch)
    response = api_client.post(CREATE_UNIT_PATH, payload)
    body = parse_json(response, "Unauthenticated create")
    if response.status != 401:
        pytest.fail(
            f"Expected HTTP 401 without a token, got {response.status}. "
            f"Details: {safe_error_summary(body)}"
        )
    assert_password_absent(body, api_config["unit_password"])


@pytest.mark.regression
def test_list_units_without_tenant_header_fails(
    _playwright_instance, api_config, auth_token
):
    """admin-service list requires x-tenant-id; Bearer alone is not enough on UAT."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    context = _playwright_instance.request.new_context(
        base_url=api_config["base_url"],
        extra_http_headers=headers,
    )
    from api.clients.api_client import ApiClient

    client = ApiClient(context, default_headers=headers)
    try:
        response = client.get(list_units_path(page=1, size=5))
        body = parse_json(response, "List without tenant")
        if response.status == 200:
            pytest.fail("List unexpectedly succeeded without x-tenant-id")
        if response.status not in (400, 401, 403, 500):
            pytest.fail(
                f"Unexpected status without tenant header: {response.status}. "
                f"Details: {safe_error_summary(body)}"
            )
    finally:
        context.dispose()


@pytest.mark.smoke
def test_authenticated_client_has_tenant_and_bearer(authenticated_api):
    auth = authenticated_api.default_headers.get("Authorization", "")
    tenant = authenticated_api.default_headers.get("x-tenant-id", "")
    if not auth.startswith("Bearer ") or len(auth) <= len("Bearer "):
        pytest.fail("Authenticated client is missing a Bearer authorization header")
    if not tenant:
        pytest.fail("Authenticated client is missing x-tenant-id")
