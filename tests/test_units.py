import json
import re

import pytest
from playwright.sync_api import expect

from helpers.unique import (
    unique_email,
    unique_first_name,
    unique_last_name,
    unique_mobile,
)
from helpers.urls import url_is
from pages.units_page import UnitsPage

with open("test_data/unit_cases.json", "r", encoding="utf-8") as file:
    unit_data = json.load(file)

BRANCH = unit_data["default_branch_code"]
PASSWORD = unit_data["password"]
CREATED_MESSAGE = "user created successfully"
UPDATED_MESSAGE = "ITACO User's Details are Updated Successfully"


@pytest.mark.smoke
def test_units_page_loads(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"))
    expect(authenticated_page.get_by_role("heading", name="Units")).to_be_visible()
    expect(units.create_button).to_be_visible()
    expect(units.create_button).to_be_enabled()
    expect(units.search).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Code")).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Actions")).to_be_visible()


@pytest.mark.regression
def test_unit_create_required_fields(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.req")
    phone = unique_mobile()
    first_name = unique_first_name()
    last_name = unique_last_name()

    units.open()
    units.open_create()
    expect(authenticated_page).to_have_url(url_is("/service-provider/units/create"))

    units.fill_required(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text(CREATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    expect(authenticated_page.get_by_role("heading", name="Other Details")).to_be_visible()
    expect(units.submit_button).to_be_disabled()

    units.back()

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_unit_create_all_fields(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.all")
    phone = unique_mobile()
    first_name = unique_first_name()
    last_name = unique_last_name()

    units.open()
    units.open_create()
    units.fill_all(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text(CREATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    units.back()

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_unit_other_details_updates_created_user(authenticated_page):
    """First Submit creates the unit. Other Details Submit updates that same row."""
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.update")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text(CREATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    expect(authenticated_page.get_by_role("heading", name="Other Details")).to_be_visible()
    expect(units.submit_button).to_be_disabled()

    units.select_language("English")
    expect(units.submit_button).to_be_enabled()
    units.submit()

    expect(
        authenticated_page.get_by_text(UPDATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_unit_create_shows_row_details(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.details")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()
    expect(
        authenticated_page.get_by_text(CREATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    units.back()

    row = units.row_containing(email)
    expect(row).to_be_visible(timeout=15_000)
    expect(units.row_by_email(email)).to_be_visible()
    # Code column is the first gridcell on the created row
    unit_code = row.get_by_role("gridcell").first
    expect(unit_code).to_be_visible()
    expect(unit_code).not_to_have_text("", timeout=5_000)


@pytest.mark.regression
def test_unit_edit_updates_first_name(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.edit")
    new_first = "Edited"

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.finish_create()
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)

    units.edit_row_by_email(email)
    expect(authenticated_page).to_have_url(
        re.compile(r".*/service-provider/users/update/"), timeout=15_000
    )
    # Wait for existing values to load before overwriting
    expect(units.first_name).not_to_have_value("", timeout=15_000)
    units.first_name.fill(new_first)
    expect(units.first_name).to_have_value(new_first)
    units.save_edit()

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    row = units.row_containing(email)
    expect(row).to_contain_text(new_first, timeout=15_000)


@pytest.mark.regression
def test_unit_delete_removes_row(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.del")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.finish_create()
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)

    units.delete_row_by_email(email)
    expect(
        authenticated_page.get_by_text("Are you sure you want to delete user")
    ).to_be_visible()
    units.confirm_dialog()

    expect(units.row_by_email(email)).to_have_count(0, timeout=15_000)


@pytest.mark.regression
def test_unit_search_filters_by_email(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.search")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.finish_create()
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)

    units.search_for("unit.search")
    expect(units.row_by_email(email)).to_be_visible(timeout=10_000)


@pytest.mark.regression
def test_unit_clear_search(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.clear")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.finish_create()

    units.search_for(email)
    expect(units.row_by_email(email)).to_be_visible(timeout=10_000)
    units.clear_search()
    expect(units.row_by_email(email)).to_be_visible(timeout=10_000)


@pytest.mark.regression
def test_unit_map_view_toggle(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()

    expect(authenticated_page.get_by_text("Map view")).to_be_visible()
    before = units.map_switch_input.is_checked()
    units.toggle_map_view()
    expect(units.map_switch_input).to_be_checked(checked=not before)


@pytest.mark.regression
def test_unit_reset_clears_first_name(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.first_name.fill("TempName")
    units.reset()

    expect(units.first_name).to_have_value("")


@pytest.mark.regression
def test_unit_delete_cancel_keeps_row(authenticated_page):
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.canceldel")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.finish_create()
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)

    units.delete_row_by_email(email)
    units.cancel_dialog()
    expect(units.row_by_email(email)).to_be_visible()


@pytest.mark.regression
def test_unit_empty_required_rejected(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.submit()

    expect(
        authenticated_page.get_by_text("First Name is required.", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Email is required.", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Country code is required.", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Phone number is required.", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Password is required.", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Confirm password is required.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_unit_alphabets_in_phone_rejected(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=unique_email("unit.phone"),
        phone="abcdefghij",
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text("Enter a valid phone number.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_unit_invalid_email_rejected(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email="not-an-email",
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text("Enter a valid email.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_unit_password_mismatch_rejected(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=unique_email("unit.mismatch"),
        phone=unique_mobile(),
        password=PASSWORD,
        confirm_password="Different@123",
        branch_code=BRANCH,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text("Passwords do not match.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_unit_create_without_branch_shows_row(authenticated_page):
    """Branch is optional. The first Submit still creates the unit."""
    units = UnitsPage(authenticated_page)
    email = unique_email("unit.nobranch")

    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=email,
        phone=unique_mobile(),
        password=PASSWORD,
        branch_code=None,
    )
    units.submit()

    expect(
        authenticated_page.get_by_text(CREATED_MESSAGE, exact=True).first
    ).to_be_visible(timeout=15_000)
    units.back()

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    expect(units.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_unit_weak_password_rejected(authenticated_page):
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.password.fill("123")
    # Blur password so field-level validation appears
    units.confirm_password.click()

    expect(
        authenticated_page.get_by_text(
            "Password should be of min 8 characters length.",
            exact=True,
        )
    ).to_be_visible()

