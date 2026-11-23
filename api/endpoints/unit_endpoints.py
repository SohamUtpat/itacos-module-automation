"""Unit (ITACO user) endpoints confirmed from the UAT Network tab."""

CREATE_UNIT_PATH = "/user-management-service/v1/user/itaco-user"
UPDATE_UNIT_PATH = "/user-management-service/v1/user/itaco-user/{unit_id}"
LIST_UNITS_PATH = "/admin-service/v1/provider-units"
DELETE_UNIT_PATH = "/admin-service/v1/provider-unit/{unit_id}"
PROVIDER_OFFICE_PATH = "/admin-service/v1/provider-office"
BRANCHES_PATH = "/admin-service/v1/provider-office-branches/{provider_id}"

DEFAULT_DEPARTMENT = "Service Providers"
DEFAULT_ROLE = "Service Provider Unit"
DEFAULT_COUNTRY_CODE = "+91"
DEFAULT_USER_STATUS = "ACTIVE"


def update_unit_path(unit_id: str) -> str:
    return UPDATE_UNIT_PATH.format(unit_id=unit_id)


def delete_unit_path(unit_id: str) -> str:
    return DELETE_UNIT_PATH.format(unit_id=unit_id)


def branches_path(provider_id: str) -> str:
    return BRANCHES_PATH.format(provider_id=provider_id)


def list_units_path(page: int = 1, size: int = 20, search: str = "", department_id: str = "") -> str:
    return (
        f"{LIST_UNITS_PATH}"
        f"?page={page}&size={size}"
        f"&search={search}&departmentId={department_id}"
    )


def build_create_unit_payload(
    *,
    first_name: str,
    email: str,
    phone: str,
    password: str,
    provider_id: str,
    branch_id: str | None,
    last_name: str = "",
    country_code: str = DEFAULT_COUNTRY_CODE,
    user_status: str = DEFAULT_USER_STATUS,
    department_name: str = DEFAULT_DEPARTMENT,
    role_name: str = DEFAULT_ROLE,
    include_branch_id: bool = True,
    include_password: bool = True,
    extra_user_fields: dict | None = None,
):
    """Build the create-unit body using the field names the API expects."""
    user_details = {
        "firstName": first_name,
        "lastName": last_name,
        "countryCode": country_code,
        "phone": phone,
        "email": email,
        "userStatus": user_status,
        "userRolesPostRequest": [
            {
                "departmentName": department_name,
                "role": [{"role": role_name}],
            }
        ],
    }
    if include_password:
        user_details["password"] = password
    if extra_user_fields:
        user_details.update(extra_user_fields)

    payload = {
        "userBasicDetailsPostRequest": user_details,
        "providerId": provider_id,
    }
    if include_branch_id:
        payload["branchId"] = branch_id
    return payload


def build_update_unit_payload(**fields):
    """Wrap update fields under userBasicDetailsPostRequest."""
    return {"userBasicDetailsPostRequest": dict(fields)}
