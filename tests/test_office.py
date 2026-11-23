import json

import pytest
from playwright.sync_api import expect

from helpers.unique import unique_email, unique_mobile, unique_suffix
from helpers.urls import url_is
from pages.office_page import OfficePage

with open("test_data/office_cases.json", "r", encoding="utf-8") as file:
    office_data = json.load(file)

UPDATED_MESSAGE = office_data["updated_message"]


def _expect_updated_toast(page) -> None:
    expect(page.get_by_text(UPDATED_MESSAGE, exact=True).first).to_be_visible(
        timeout=15_000
    )


def _unique_office_required(data: dict) -> dict:
    """Build required office values that differ each run so Save is a real update."""
    suffix = unique_suffix()
    return {
        "company_name": f"{data['company_name']} {suffix[-6:]}",
        "short_name": data["short_name"],  # keep stable short code
        "mobile": unique_mobile(),
        "email": unique_email("office"),
        "location_query": data["location_query"],
    }


# --- Negative cases (first) ---


@pytest.mark.regression
@pytest.mark.negative
def test_office_empty_company_name_shows_error(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.company_name.fill("")
    office.save()

    expect(
        authenticated_page.get_by_text("Company name is required", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_alphabets_in_mobile_rejected(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.mobile_number.fill("abcdefghij")
    office.save()

    expect(
        authenticated_page.get_by_text("Please enter valid mobile number", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_invalid_email_rejected(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.email.fill("not-an-email")
    office.save()

    expect(
        authenticated_page.get_by_text("Enter a valid email.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_empty_short_name_shows_error(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.short_name.fill("")
    office.save()

    expect(
        authenticated_page.get_by_text("Short name is required", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_empty_email_shows_error(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.email.fill("")
    office.save()

    expect(
        authenticated_page.get_by_text("Email is required.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_empty_mobile_shows_error(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.mobile_number.fill("")
    office.save()

    expect(
        authenticated_page.get_by_text("Mobile number is required", exact=True)
    ).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
def test_office_invalid_landline_rejected(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.landline.fill("abcdefghi")
    office.save()

    expect(
        authenticated_page.get_by_text(
            "Please enter valid Landline number",
            exact=True,
        )
    ).to_be_visible()


# --- Positive / smoke (after negatives) ---


@pytest.mark.smoke
def test_office_details_page_loads(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()

    expect(authenticated_page).to_have_url(
        url_is("/service-provider/provider-office/manage-office")
    )
    expect(
        authenticated_page.get_by_role("heading", name="Provider Office Onboarding")
    ).to_be_visible()
    expect(office.company_name).to_be_visible()
    expect(office.save_button).to_be_visible()
    expect(office.reset_button).to_be_visible()


@pytest.mark.regression
def test_office_save_required_fields(authenticated_page):
    data = _unique_office_required(office_data["happy_required"])
    office = OfficePage(authenticated_page)
    office.open()

    office.fill_required(
        company_name=data["company_name"],
        short_name=data["short_name"],
        mobile=data["mobile"],
        email=data["email"],
        location_query=data["location_query"],
    )
    office.save()
    _expect_updated_toast(authenticated_page)

    expect(office.company_name).to_have_value(data["company_name"])
    expect(office.short_name).to_have_value(data["short_name"])
    expect(office.mobile_number).to_have_value(data["mobile"])
    expect(office.email).to_have_value(data["email"])
    expect(
        authenticated_page.get_by_role("heading", name="Provider Office Onboarding")
    ).to_be_visible()


@pytest.mark.regression
def test_office_save_all_fields(authenticated_page):
    base = office_data["happy_all_fields"]
    data = _unique_office_required(base)
    comments = f"{base['comments']} {unique_suffix()}"
    landline = base["landline"]
    office = OfficePage(authenticated_page)
    office.open()

    office.fill_required(
        company_name=data["company_name"],
        short_name=data["short_name"],
        mobile=data["mobile"],
        email=data["email"],
        location_query=data["location_query"],
    )
    office.fill_optional(landline=landline, comments=comments)
    office.save()
    _expect_updated_toast(authenticated_page)

    expect(office.company_name).to_have_value(data["company_name"])
    expect(office.mobile_number).to_have_value(data["mobile"])
    expect(office.email).to_have_value(data["email"])
    expect(office.landline).to_have_value(landline)
    expect(office.comments).to_have_value(comments)


@pytest.mark.regression
def test_office_save_persists_after_reload(authenticated_page):
    data = _unique_office_required(office_data["happy_required"])
    office = OfficePage(authenticated_page)
    office.open()
    office.fill_required(
        company_name=data["company_name"],
        short_name=data["short_name"],
        mobile=data["mobile"],
        email=data["email"],
        location_query=data["location_query"],
    )
    office.save()
    _expect_updated_toast(authenticated_page)
    office.reload()

    expect(office.company_name).to_have_value(data["company_name"])
    expect(office.short_name).to_have_value(data["short_name"])
    expect(office.mobile_number).to_have_value(data["mobile"])
    expect(office.email).to_have_value(data["email"])


@pytest.mark.regression
def test_office_update_comments_and_save(authenticated_page):
    # Unique value so Save sees a real change (avoids "at least one field must be updated")
    comments = f"Automation updated comments {unique_suffix()}"
    office = OfficePage(authenticated_page)
    office.open()
    office.comments.fill(comments)
    office.save()
    _expect_updated_toast(authenticated_page)
    office.reload()

    expect(office.comments).to_have_value(comments)


@pytest.mark.regression
def test_office_save_bank_details(authenticated_page):
    data = office_data["happy_required"]
    bank = office_data["bank_details"]
    # Unique account so this is a real update each run
    account_number = f"{bank['account_number'][:-4]}{unique_suffix()[-4:]}"
    office = OfficePage(authenticated_page)
    office.open()
    office.fill_bank_details(
        account_number=account_number,
        iban_code=bank["iban_code"],
        branch=bank["branch"],
    )
    office.save()
    _expect_updated_toast(authenticated_page)

    expect(office.account_number).to_have_value(account_number)
    expect(office.iban_code).to_have_value(bank["iban_code"])
    expect(office.bank_branch).to_have_value(bank["branch"])


@pytest.mark.regression
def test_office_active_hours_section(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    office.go_section("Active Hours")

    expect(authenticated_page.get_by_role("heading", name="Active Hours")).to_be_visible()
    saturday = authenticated_page.get_by_role("checkbox", name="SATURDAY").first
    before = saturday.is_checked()
    office.toggle_day("SATURDAY")
    expect(saturday).to_be_checked(checked=not before)
    # Restore prior state so other tests stay stable
    office.toggle_day("SATURDAY")
    office.save()


@pytest.mark.regression
def test_office_network_type_currency_visible(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()

    expect(authenticated_page.locator("label").filter(has_text="Network Type")).to_be_visible()
    expect(authenticated_page.locator("label").filter(has_text="Currency")).to_be_visible()
    expect(office.payable_days).to_be_visible()
    expect(office.network_type).to_be_visible()
    expect(office.currency).to_be_visible()


@pytest.mark.regression
def test_office_view_history_opens(authenticated_page):
    """View History opens the status-history grid (not a field-level audit log).

    Columns are Status / Comment / Updated By / Updated Date & Time.
    Normal form edits (Comments, bank, mobile, etc.) do not create rows here.
    """
    office = OfficePage(authenticated_page)
    office.open()
    office.open_view_history()

    expect(
        authenticated_page.get_by_role("columnheader", name="Status")
    ).to_be_visible()
    expect(
        authenticated_page.get_by_role("columnheader", name="Comment")
    ).to_be_visible()
    expect(
        authenticated_page.get_by_role("columnheader", name="Updated By")
    ).to_be_visible()
    expect(
        authenticated_page.get_by_role(
            "columnheader", name="Updated Date & Time"
        )
    ).to_be_visible()


@pytest.mark.regression
def test_office_reset_restores_unsaved_comments(authenticated_page):
    office = OfficePage(authenticated_page)
    office.open()
    original = office.comments.input_value()
    office.comments.fill("TEMP unsaved comments for reset")
    office.reset()

    expect(office.comments).to_have_value(original)
