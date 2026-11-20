"""Login endpoint confirmed from the UAT Network tab."""

LOGIN_PATH = "/user-management-service/v1/login"


def build_login_payload(
    user_name,
    password,
    app_type="WEB",
    force_login=True,
    include_user_name=True,
    include_password=True,
):
    """Build the login body using the field names the API expects.

    userName, password, appType, and forceLogin must stay spelled this way.
    """
    payload = {
        "appType": app_type,
        "forceLogin": force_login,
    }
    if include_user_name:
        payload["userName"] = user_name
    if include_password:
        payload["password"] = password
    return payload
