import json
import re

import pytest
from playwright.sync_api import expect

from helpers.unique import unique_email, unique_mobile
from helpers.urls import url_is
from pages.workshops_page import WorkshopsPage

with open("test_data/workshop_cases.json", "r", encoding="utf-8") as file:
    workshop_data = json.load(file)

LOCATION = workshop_data["location_query"]
LANDLINE = workshop_data["landline"]


def _fill_required(workshops: WorkshopsPage, mobile: str, email: str, **overrides):
    workshops.fill_required(
        mobile=mobile,
        email=email,
        location_query=overrides.pop("location_query", LOCATION),
        landline=overrides.pop("landline", LANDLINE),
        brand=workshop_data["brand"],
        workshop_type=workshop_data["workshop_type"],
        fuel_type=workshop_data["fuel_type"],
        repair_type=workshop_data["repair_type"],
        priority=workshop_data["priority"],
        **overrides,
    )


@pytest.mark.smoke
def test_workshops_page_loads(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()

    expect(authenticated_page).to_have_url(url_is("/service-provider/garages"))
    expect(authenticated_page.get_by_role("heading", name="Workshops")).to_be_visible()
    expect(workshops.create_button).to_be_visible()
    expect(workshops.create_button).to_be_enabled()
    expect(authenticated_page.get_by_text("Map view")).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Code")).to_be_visible()
    expect(
        authenticated_page.get_by_role("columnheader", name="Contact Email")
    ).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="City")).to_be_visible()
    expect(
        authenticated_page.get_by_role("columnheader", name="Contact Number")
    ).to_be_visible()
    expect(
        authenticated_page.get_by_role("columnheader", name="Landline Number")
    ).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Status")).to_be_visible()
    expect(authenticated_page.get_by_role("columnheader", name="Actions")).to_be_visible()


@pytest.mark.regression
def test_workshop_create_required_fields(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.req")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    expect(authenticated_page).to_have_url(url_is("/service-provider/garages/create"))

    _fill_required(workshops, mobile, email)
    workshops.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/garages"), timeout=20_000)
    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_workshop_create_all_fields(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.all")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    workshops.fill_all(
        mobile=mobile,
        email=email,
        location_query=LOCATION,
        landline=LANDLINE,
        alt_mobile=unique_mobile(),
        whatsapp=unique_mobile(),
        alt_landline="21234568",
        teams_id="auto.teams",
        po_box="411046",
    )
    workshops.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/garages"), timeout=20_000)
    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_workshop_create_shows_row_details(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.details")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    _fill_required(workshops, mobile, email)
    workshops.save()

    row = workshops.row_containing(email)
    expect(row).to_be_visible(timeout=15_000)
    expect(row.get_by_role("gridcell", name="Pune")).to_be_visible()
    expect(row.get_by_role("gridcell", name=mobile)).to_be_visible()
    expect(row.get_by_role("gridcell", name=LANDLINE)).to_be_visible()
    expect(row.get_by_role("gridcell", name="Active")).to_be_visible()
    code = workshops.code_from_email_row(email)
    assert code, "Expected a workshop Code on the created row"


@pytest.mark.regression
def test_workshop_edit_updates_mobile(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.edit")
    mobile = unique_mobile()
    # unique_mobile() is second-based, so a second call in this test can match.
    new_mobile = f"8{mobile[1:]}"

    workshops.open()
    workshops.open_create()
    _fill_required(workshops, mobile, email)
    workshops.save()
    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)

    workshops.edit_row_by_email(email)
    expect(authenticated_page).to_have_url(
        re.compile(r".*/service-provider/garages/update/"), timeout=15_000
    )
    expect(workshops.mobile_number).not_to_have_value("", timeout=15_000)
    expect(workshops.email).to_have_value(email, timeout=15_000)
    workshops.mobile_number.fill(new_mobile)
    expect(workshops.mobile_number).to_have_value(new_mobile)
    # Blur so the edit form registers the change before Save opens the dialog.
    workshops.email.click()
    if not (workshops.country.input_value() or "").strip():
        workshops.pick_location(LOCATION)
    workshops.save()

    expect(authenticated_page).to_have_url(url_is("/service-provider/garages"), timeout=20_000)
    row = workshops.row_containing(email)
    expect(row.get_by_role("gridcell", name=new_mobile)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_workshop_delete_removes_row(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.del")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    _fill_required(workshops, mobile, email)
    workshops.save()
    expect(authenticated_page).to_have_url(url_is("/service-provider/garages"), timeout=20_000)
    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)
    code = workshops.code_from_email_row(email)
    assert code, "Expected a workshop Code on the created row"

    workshops.delete_row_by_email(email)
    expect(
        authenticated_page.get_by_text("Are you sure you want to delete workshop")
    ).to_be_visible()
    workshops.confirm_dialog()

    expect(workshops.row_by_email(email)).to_have_count(0, timeout=15_000)
    expect(workshops.row_by_code(code)).to_have_count(0, timeout=15_000)


@pytest.mark.regression
def test_workshop_delete_cancel_keeps_row(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.keep")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    _fill_required(workshops, mobile, email)
    workshops.save()
    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)

    workshops.delete_row_by_email(email)
    workshops.cancel_dialog()

    expect(workshops.row_by_email(email)).to_be_visible()


@pytest.mark.regression
def test_workshop_map_view_toggle(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()

    expect(authenticated_page.get_by_text("Map view")).to_be_visible()
    expect(workshops.map_switch_input).to_be_enabled(timeout=20_000)
    before = workshops.map_switch_input.is_checked()
    workshops.toggle_map_view()
    expect(workshops.map_switch_input).to_be_checked(checked=not before, timeout=10_000)


@pytest.mark.regression
def test_workshop_reset_clears_mobile(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    workshops.mobile_number.fill(unique_mobile())
    workshops.reset()

    expect(workshops.mobile_number).to_have_value("")


@pytest.mark.regression
def test_workshop_create_custom_working_days(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.days")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    _fill_required(
        workshops,
        mobile,
        email,
        days=["MONDAY", "TUESDAY", "WEDNESDAY"],
    )
    workshops.save()

    expect(workshops.row_by_email(email)).to_be_visible(timeout=15_000)


@pytest.mark.regression
def test_workshop_confirm_cancel_stays_on_form(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    email = unique_email("workshop.cancel")
    mobile = unique_mobile()

    workshops.open()
    workshops.open_create()
    _fill_required(workshops, mobile, email)
    workshops.save(confirm=False)

    expect(authenticated_page).to_have_url(url_is("/service-provider/garages/create"))
    workshops.open()
    expect(workshops.row_by_email(email)).to_have_count(0)


@pytest.mark.regression
def test_workshop_empty_required_rejected(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    workshops.save()

    expect(authenticated_page.get_by_text("Fuel type is Required")).to_be_visible()
    expect(authenticated_page.get_by_text("Mobile number is required")).to_be_visible()
    expect(authenticated_page.get_by_text("Landline number is required")).to_be_visible()
    expect(authenticated_page.get_by_text("Email is required.")).to_be_visible()
    expect(authenticated_page.get_by_text("Please select at least one day")).to_be_visible()
    expect(authenticated_page.get_by_text("Country is required")).to_be_visible()
    expect(authenticated_page.get_by_text("Address is required")).to_be_visible()


@pytest.mark.regression
def test_workshop_alphabets_in_mobile_rejected(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    workshops.mobile_number.fill("abcdefghij")
    workshops.email.click()

    expect(
        authenticated_page.get_by_text(
            "Please enter valid mobile number", exact=True
        )
    ).to_be_visible()


@pytest.mark.regression
def test_workshop_invalid_email_rejected(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    workshops.mobile_number.fill(unique_mobile())
    workshops.email.fill("bad-email")
    workshops.save()

    expect(
        authenticated_page.get_by_text("Enter a valid email.", exact=True)
    ).to_be_visible()


@pytest.mark.regression
def test_workshop_invalid_landline_rejected(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    workshops.mobile_number.fill(unique_mobile())
    workshops.email.fill(unique_email("workshop.ll"))
    workshops.landline.fill("abcdefgh")
    workshops.save()

    expect(
        authenticated_page.get_by_text(
            "Please enter valid Landline number", exact=True
        )
    ).to_be_visible()


@pytest.mark.regression
def test_workshop_no_location_rejected(authenticated_page):
    workshops = WorkshopsPage(authenticated_page)
    workshops.open()
    workshops.open_create()
    _fill_required(
        workshops,
        unique_mobile(),
        unique_email("workshop.noloc"),
        location_query=None,
        pick_location_flag=False,
    )
    workshops.save()

    expect(
        authenticated_page.get_by_text("Country is required", exact=True)
    ).to_be_visible()
    expect(
        authenticated_page.get_by_text("Address is required", exact=True)
    ).to_be_visible()
