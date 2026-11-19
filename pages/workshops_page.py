from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect

from helpers.location import pick_location


DEFAULT_WORKING_DAYS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
]


class WorkshopsPage:

    def __init__(self, page: Page):
        self.page = page
        self.create_button = page.get_by_role("button", name="Create Workshop")
        self.save_button = page.get_by_role("button", name="Save")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.brand_select = page.locator("#mui-component-select-brandDetailIDs")
        self.workshop_type_select = page.locator("#mui-component-select-workshopTypeIDs")
        self.fuel_type_select = page.locator("#mui-component-select-fuelTypes")
        self.repair_type_select = page.locator("#mui-component-select-repairTypes")
        self.priority = page.locator("#priority")
        self.mobile_number = page.locator(
            'input[name="contactPostRequest.mobileNumber"]'
        )
        self.alt_mobile = page.locator(
            'input[name="contactPostRequest.alternativeMobileNumber"]'
        )
        self.whatsapp = page.locator('input[name="contactPostRequest.whatsAppNumber"]')
        self.landline = page.locator('input[name="contactPostRequest.landLineNumber"]')
        self.alt_landline = page.locator(
            'input[name="contactPostRequest.alternativeLandLineNumber"]'
        )
        self.email = page.locator('input[name="contactPostRequest.email"]')
        self.teams_id = page.locator('input[name="contactPostRequest.teamsId"]')
        self.po_box = page.locator('input[name="addressPostRequest.pOBoxNumber"]')
        self.country = page.locator('input[name="addressPostRequest.country"]')
        self.map_switch = page.locator(".MuiSwitch-root").first
        self.map_switch_input = page.locator(".MuiSwitch-input").first

    def open(self):
        """Open the Workshops list; reload once if Create Workshop never appears."""
        self.page.get_by_role("button", name="Workshops", exact=True).click()
        self.page.get_by_role("heading", name="Workshops").wait_for(
            state="visible", timeout=20_000
        )
        try:
            self.create_button.wait_for(state="visible", timeout=15_000)
        except PlaywrightTimeout:
            self.page.reload()
            self.page.get_by_role("heading", name="Workshops").wait_for(
                state="visible", timeout=20_000
            )
            self.create_button.wait_for(state="visible", timeout=20_000)

        expect(self.create_button).to_be_enabled(timeout=20_000)
        try:
            expect(self.map_switch_input).to_be_enabled(timeout=10_000)
        except AssertionError:
            pass

    def open_create(self):
        self.create_button.click()
        self.mobile_number.wait_for(state="visible", timeout=15_000)

    def _choose(self, combo, option_name: str):
        """Open a MUI select and choose an option. Escape closes multi-selects."""
        combo.scroll_into_view_if_needed()
        current = (combo.inner_text() or "").replace("\u200b", "").strip()
        if option_name and option_name in current:
            return

        combo.click()
        option = self.page.get_by_role("option", name=option_name, exact=True)
        option.wait_for(state="visible", timeout=5_000)
        option.click()
        self.page.keyboard.press("Escape")

    def select_working_days(self, days: list[str] | None = None):
        days = days or DEFAULT_WORKING_DAYS
        for day in days:
            box = self.page.get_by_role("checkbox", name=day)
            box.scroll_into_view_if_needed()
            if not box.is_checked():
                try:
                    box.check(timeout=3_000)
                except Exception:
                    box.click(force=True)

        for hours in self.page.get_by_role("checkbox", name="24 Hours").all():
            if hours.is_visible() and not hours.is_checked():
                try:
                    hours.check(timeout=3_000)
                except Exception:
                    hours.click(force=True)

    def fill_required(
        self,
        mobile: str,
        email: str,
        location_query: str | None = None,
        landline: str = "21234567",
        days: list[str] | None = None,
        pick_location_flag: bool = True,
        brand: str = "Toyota",
        workshop_type: str = "Mechanical",
        fuel_type: str = "Petrol",
        repair_type: str = "General Repair",
        priority: str = "1",
    ):
        if brand:
            self._choose(self.brand_select, brand)
        if workshop_type:
            self._choose(self.workshop_type_select, workshop_type)
        if fuel_type:
            self._choose(self.fuel_type_select, fuel_type)
        if priority:
            self.priority.fill(priority)
        if repair_type:
            self._choose(self.repair_type_select, repair_type)
        if mobile:
            self.mobile_number.fill(mobile)
        if email:
            self.email.fill(email)
        if landline:
            self.landline.fill(landline)
        self.select_working_days(days)
        if pick_location_flag and location_query:
            self.pick_location(location_query)

    def fill_all(
        self,
        mobile: str,
        email: str,
        location_query: str,
        landline: str = "21234567",
        alt_mobile: str = "",
        whatsapp: str = "",
        alt_landline: str = "",
        teams_id: str = "",
        po_box: str = "",
    ):
        self.fill_required(
            mobile=mobile,
            email=email,
            location_query=location_query,
            landline=landline,
        )
        if alt_mobile:
            self.alt_mobile.fill(alt_mobile)
        if whatsapp:
            self.whatsapp.fill(whatsapp)
        if alt_landline:
            self.alt_landline.fill(alt_landline)
        if teams_id:
            self.teams_id.fill(teams_id)
        if po_box:
            self.po_box.fill(po_box)

    def pick_location(self, query: str):
        pick_location(self.page, query, country_locator=self.country)

    def save(self, confirm: bool = True):
        self.save_button.click()
        dialog = self.page.get_by_role("dialog")
        try:
            dialog.wait_for(state="visible", timeout=8_000)
            if confirm:
                dialog.get_by_role("button", name="Confirm").click()
            else:
                dialog.get_by_role("button", name="Cancel").click()
        except PlaywrightTimeout:
            pass

    def reset(self):
        self.reset_button.click()

    def toggle_map_view(self):
        expect(self.map_switch_input).to_be_enabled(timeout=20_000)
        self.page.get_by_text("Map view").locator("..").locator(
            ".MuiSwitch-root"
        ).click()

    def row_by_email(self, email: str):
        return self.page.get_by_role("gridcell", name=email)

    def row_by_code(self, code: str):
        return self.page.get_by_role("gridcell", name=code)

    def row_containing(self, email: str):
        return self.page.locator(f"[role='row']:has-text('{email}')")

    def code_from_email_row(self, email: str) -> str:
        cell = self.row_containing(email).get_by_role("gridcell").first
        expect(cell).to_be_visible(timeout=15_000)
        return (cell.inner_text() or "").strip()

    def edit_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Edit").click()
        self.mobile_number.wait_for(state="visible", timeout=15_000)

    def delete_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Delete").click()

    def confirm_dialog(self):
        self.page.get_by_role("dialog").get_by_role("button", name="Confirm").click()

    def cancel_dialog(self):
        self.page.get_by_role("dialog").get_by_role("button", name="Cancel").click()
