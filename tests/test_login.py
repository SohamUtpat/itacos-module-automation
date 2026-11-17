import json
import os

import pytest
from playwright.sync_api import expect

from pages.login_page import LoginPage


with open("test_data/login_users.json", "r", encoding="utf-8") as file:
    users = json.load(file)


def _resolve(user: dict) -> tuple[str, str]:
    env_id = os.getenv("LOGIN_EMAIL_OR_MOBILE", "")
    env_mobile = os.getenv("LOGIN_MOBILE", "")
    password = os.getenv("LOGIN_PASSWORD", "")

    email_or_mobile = user["email_or_mobile"]
    pwd = user["password"]

    if email_or_mobile == "ENV":
        email_or_mobile = env_id
    elif email_or_mobile == "ENV_MOBILE":
        if not env_mobile:
            pytest.skip("LOGIN_MOBILE is not set in .env — required for TC-L02")
        email_or_mobile = env_mobile
    elif email_or_mobile == "CASE_EMAIL":
        email_or_mobile = env_id.swapcase() if env_id else ""
    elif email_or_mobile == "SPACES_EMAIL":
        email_or_mobile = f"  {env_id}  " if env_id else "  "

    if pwd == "ENV":
        pwd = password
    elif pwd == "CASE":
        # wrong letter case of the real password
        pwd = password.swapcase() if password else "WrongCase"
    elif pwd == "SPACES_PASSWORD":
        pwd = f"  {password}  " if password else "  "

    return email_or_mobile, pwd


def _marks_for(user: dict):
    marks = [getattr(pytest.mark, user.get("mark", "regression"))]
    if user.get("xfail"):
        # Known product gap vs standard; drop xfail once UAT matches.
        marks.append(pytest.mark.xfail(reason=user["xfail"], strict=False))
    return marks


@pytest.mark.parametrize(
    "user",
    [
        pytest.param(user, marks=_marks_for(user), id=user["id"])
        for user in users
    ],
)
def test_login(login_page, user):
    email_or_mobile, password = _resolve(user)
    login = LoginPage(login_page)

    # TC-L03 — password field masks input (no submit)
    if user["expected"] == "masked":
        login.enter_password(password or "AnyPassword1")
        expect(login.password).to_have_attribute("type", "password")
        return

    login.login(email_or_mobile, password)

    # success path (TC-L01, TC-L02, and format cases that should still log in)
    if user["expected"] == "success":
        if not os.getenv("LOGIN_PASSWORD"):
            pytest.fail("LOGIN_PASSWORD must be set in .env")
        if user["email_or_mobile"] != "ENV_MOBILE" and not os.getenv("LOGIN_EMAIL_OR_MOBILE"):
            pytest.fail("LOGIN_EMAIL_OR_MOBILE must be set in .env")

        expect(login_page).to_have_title("Assist Me")
        expect(login_page.get_by_text("Provider Office Admin")).to_be_visible()

    # negative cases — stay on login and show the expected error(s)
    else:
        expect(login_page.get_by_role("heading", name="Welcome Back")).to_be_visible()

        messages = user.get("error_messages")
        if messages is None:
            messages = [user["error_message"]]

        # App toast text uses the trimmed email even when spaces were typed
        resolved_email = email_or_mobile.strip()
        for message in messages:
            message = message.replace("{email}", resolved_email)
            # Toasts auto-dismiss in a few seconds; use .first (duplicate nodes)
            # and a longer timeout so slow API responses do not flake.
            expect(login_page.get_by_text(message).first).to_be_visible(timeout=10_000)
