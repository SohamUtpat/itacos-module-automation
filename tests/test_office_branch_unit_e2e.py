import json

import pytest
from playwright.sync_api import expect

from helpers.unique import (
    unique_email,
    unique_first_name,
    unique_last_name,
    unique_mobile,
)
from helpers.urls import url_is
from pages.branches_page import BranchesPage
from pages.office_page import OfficePage
from pages.units_page import UnitsPage

with open("test_data/office_cases.json", "r", encoding="utf-8") as file:
    office_data = json.load(file)

with open("test_data/branch_cases.json", "r", encoding="utf-8") as file:
    branch_data = json.load(file)

with open("test_data/unit_cases.json", "r", encoding="utf-8") as file:
    unit_data = json.load(file)


@pytest.mark.e2e
@pytest.mark.smoke
def test_office_branch_unit_happy_path(authenticated_page):
    """Login → ensure Office → create Branch → create Unit → both rows visible."""
    office_case = office_data["happy_required"]
    location = branch_data["location_query"]
    password = unit_data["password"]

    branch_email = unique_email("e2e.branch")
    branch_mobile = unique_mobile()
    unit_email = unique_email("e2e.unit")
    unit_phone = unique_mobile()
    unit_first = unique_first_name()
    unit_last = unique_last_name()

    # 1) Office ready (save required fields on existing office)
    office = OfficePage(authenticated_page)
    office.open()
    office.fill_required(
        company_name=office_case["company_name"],
        short_name=office_case["short_name"],
        mobile=office_case["mobile"],
        email=office_case["email"],
        location_query=office_case["location_query"],
    )
    office.save()
    expect(office.company_name).to_have_value(office_case["company_name"])

    # 2) Create branch with required fields
    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=branch_mobile,
        email=branch_email,
        location_query=location,
        landline="21234567",
    )
    branches.save()
    expect(authenticated_page).to_have_url(url_is("/service-provider/branches"), timeout=20_000)
    expect(branches.row_by_email(branch_email)).to_be_visible(timeout=15_000)

    # New branch code appears in the Code column of the same row — read from grid
    # For unit create, use the latest branch code from the first Code cell if needed.
    # Seeded SP-B008 always works; prefer the just-created row's code when present.
    branch_code_cell = authenticated_page.locator(
        f"[role='row']:has-text('{branch_email}') [role='gridcell']"
    ).first
    branch_code = branch_code_cell.inner_text().strip() or unit_data["default_branch_code"]

    # 3) Create unit linked to that branch
    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.fill_required(
        first_name=unit_first,
        last_name=unit_last,
        email=unit_email,
        phone=unit_phone,
        password=password,
        branch_code=branch_code,
    )
    units.finish_create(location_query=location)

    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)
    expect(units.row_by_email(unit_email)).to_be_visible(timeout=15_000)


@pytest.mark.e2e
@pytest.mark.regression
def test_branch_unit_edit_then_search(authenticated_page):
    """Create branch + unit → edit unit name → search finds updated name."""
    location = branch_data["location_query"]
    password = unit_data["password"]
    branch_email = unique_email("e2e2.branch")
    unit_email = unique_email("e2e2.unit")
    # First name rejects digits — keep alphabetic only
    edited_first = "EditedName"

    branches = BranchesPage(authenticated_page)
    branches.open()
    branches.open_create()
    branches.fill_required(
        mobile=unique_mobile(),
        email=branch_email,
        location_query=location,
        landline="21234567",
    )
    branches.save()
    expect(branches.row_by_email(branch_email)).to_be_visible(timeout=15_000)

    branch_code = (
        authenticated_page.locator(
            f"[role='row']:has-text('{branch_email}') [role='gridcell']"
        )
        .first.inner_text()
        .strip()
        or unit_data["default_branch_code"]
    )

    units = UnitsPage(authenticated_page)
    units.open()
    units.open_create()
    units.fill_required(
        first_name=unique_first_name(),
        last_name=unique_last_name(),
        email=unit_email,
        phone=unique_mobile(),
        password=password,
        branch_code=branch_code,
    )
    units.finish_create(location_query=location)
    expect(units.row_by_email(unit_email)).to_be_visible(timeout=15_000)

    units.edit_row_by_email(unit_email)
    expect(units.first_name).not_to_have_value("", timeout=15_000)
    units.first_name.fill(edited_first)
    expect(units.first_name).to_have_value(edited_first)
    units.save_edit()
    expect(authenticated_page).to_have_url(url_is("/service-provider/units"), timeout=20_000)

    units.search_for(unit_email)
    row = units.row_containing(unit_email)
    expect(row).to_be_visible(timeout=10_000)
    expect(row).to_contain_text(edited_first)


@pytest.mark.e2e
@pytest.mark.regression
def test_create_unit_enabled_when_branches_exist(authenticated_page):
    """With existing branches, Create Unit stays enabled on Units list."""
    units = UnitsPage(authenticated_page)
    units.open()
    expect(units.create_button).to_be_visible()
    expect(units.create_button).to_be_enabled()
