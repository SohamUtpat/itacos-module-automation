import json
import re

import pytest
from playwright.sync_api import expect

from helpers.unique import unique_email, unique_mobile
from helpers.urls import url_is
from pages.branches_page import BranchesPage

with open("test_data/branch_cases.json", "r", encoding="utf-8") as file:
    branch_data = json.load(file)

LOCATION = branch_data["location_query"]


# --- Negative cases (first) ---


@pytest.mark.regression
def test_branch_empty_required_rejected(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.save()

    expect(authenticated_page.get_by_text("Mobile number is required")).to_be_visible()
    expect(authenticated_page.get_by_text("Landline number is required")).to_be_visible()
    expect(authenticated_page.get_by_text("Email is required.")).to_be_visible()
    expect(authenticated_page.get_by_text("Please select at least one day")).to_be_visible()


@pytest.mark.regression
def test_branch_alphabets_in_mobile_rejected(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.mobile_number.fill("abcdefghij")
    # Blur mobile so field-level validation appears
    branches.email.click()

    expect(
        authenticated_page.get_by_text(
            "Please enter valid mobile number", exact=True
        )
    ).to_be_visible()


@pytest.mark.regression
def test_branch_invalid_email_rejected(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.mobile_number.fill(unique_mobile())
    branches.email.fill("bad-email")
    branches.save()

    expect(
        authenticated_page.get_by_text("Enter a valid email.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_branch_invalid_landline_rejected(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.mobile_number.fill(unique_mobile())
    branches.email.fill(unique_email("branch.ll"))
    branches.landline.fill("abcdefgh")
    branches.save()

    expect(
        authenticated_page.get_by_text(
            "Please enter valid Landline number", exact=True
        )
    ).to_be_visible()


@pytest.mark.regression
def test_branch_no_location_rejected(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=unique_mobile(),
        email=unique_email("branch.noloc"),
        location_query=None,
        landline="21234567",
        pick_location_flag=False,
    )
    branches.save()

    expect(
        authenticated_page.get_by_text("Country is required", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Address is required", exact=True)
    ).to_be_visible()


# --- Positive / smoke (after negatives) ---


@pytest.mark.smoke
def test_branches_page_loads(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()

    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"))
    expect(authenticated_page.get_by_role("heading", name="Branches")).to_be_visible()
    expect(branches.create_button).to_be_visible()
    expect(branches.create_button).to_be_enabled()
    expect(authenticated_page.get_by_role("columnheader", name="Code")).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Actions")).to_be_visible()


@pytest.mark.regression
def test_branch_create_required_fields(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.req")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    expect(authenticated_page).to_have_url(url_is("/service-provider/branches/create"))

    branches.fill_required(
        mobile=mobile,
        email=email,
        location_query=LOCATION,
        landline="21234567",
    )
    branches.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"), timeout=20_000)
    expect(branches.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_branch_create_all_fields(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.all")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_all(
        mobile=mobile,
        email=email,
        location_query=LOCATION,
        alt_mobile=unique_mobile(),
        whatsapp=unique_mobile(),
        landline="21234567",
        teams_id="auto.teams",
        po_box="411046",
    )
    branches.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"), timeout=20_000)
    expect(branches.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_branch_create_shows_row_details(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.details")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=mobile, email=email, location_query=LOCATION, landline="21234567"
    )
    branches.save()

    row = branches.row_containing(email)
    expect(row).to_be_visible(timeout=15_000)
    expect(row.get_by_role("gridcell", name="Pune")).to_be_visible()
    expect(row.get_by_role("gridcell", name=mobile)).to_be_visible()
    expect(row.get_by_role("gridcell", name="Active")).to_be_visible()


@pytest.mark.regression
def test_branch_edit_updates_mobile(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.edit")
    mobile = unique_mobile()
    new_mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=mobile, email=email, location_query=LOCATION, landline="21234567"
    )
    branches.save()
    expect(branches.row_by_email(email)).to_be_visible(timeout=15_000)

    branches.edit_row_by_email(email)
    expect(authenticated_page).to_have_url(
        re.compile(r".*/service-provider/branches/update/"), timeout=15_000
    )
    # Wait for existing values to load before overwriting
    expect(branches.mobile_number).not_to_have_value("", timeout=15_000)
    expect(branches.email).to_have_value(email, timeout=15_000)
    branches.mobile_number.fill(new_mobile)
    expect(branches.mobile_number).to_have_value(new_mobile)
    # Edit form often leaves Country empty even when address text is present
    if not (branches.country.input_value() or "").strip():
        branches.pick_location(LOCATION)
    branches.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"), timeout=20_000)
    row = branches.row_containing(email)
    expect(row.get_by_role("gridcell", name=new_mobile)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_branch_delete_removes_row(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.del")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=mobile, email=email, location_query=LOCATION, landline="21234567"
    )
    branches.save()
    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"), timeout=20_000)
    expect(branches.row_by_email(email)).to_be_visible(timeout=15_000)
    branch_code = branches.code_from_email_row(email)
    assert branch_code, "Expected a branch Code on the created row"

    branches.delete_row_by_email(email)
    expect(authenticated_page.get_by_text("Are you sure", exact=False)).to_be_visible()
    branches.confirm_dialog()

    expect(branches.row_by_email(email)).to_have_count(0, timeout=15_000)
    expect(branches.row_by_code(branch_code)).to_have_count(0, timeout=15_000)


@pytest.mark.regression
def test_branch_map_view_toggle(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()

    expect(authenticated_page.get_by_text("Map view")).to_be_visible()
    expect(branches.map_switch_input).to_be_enabled(timeout=20_000)
    before = branches.map_switch_input.is_checked()
    branches.toggle_map_view()
    expect(branches.map_switch_input).to_be_checked(checked=not before, timeout=10_000)


@pytest.mark.regression
def test_branch_reset_clears_mobile(authenticated_page):
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.mobile_number.fill(unique_mobile())
    branches.reset()

    expect(branches.mobile_number).to_have_value("")


@pytest.mark.regression
def test_branch_create_custom_working_days(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.days")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=mobile,
        email=email,
        location_query=LOCATION,
        landline="21234567",
        days=["MONDAY", "TUESDAY", "WEDNESDAY"],
    )
    branches.save()

    expect(branches.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_branch_confirm_cancel_stays_on_form(authenticated_page):
    branches = BranchesPage(authenticated_page)
    email = unique_email("branch.cancel")
    mobile = unique_mobile()

    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=mobile, email=email, location_query=LOCATION, landline="21234567"
    )
    branches.save(confirm=False)

    expect(authenticated_page).to_have_url(url_is("/service-provider/branches/create"))
    branches.open()
    expect(branches.row_by_email(email)).to_have_count(0)
