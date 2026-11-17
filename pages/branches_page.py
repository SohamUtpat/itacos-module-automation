from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect

from helpers.location import pick_location


DEFAULT_WORKING_DAYS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
]


class BranchesPage:

    def __init__(self, page: Page):
        self.page = page
        self.create_button = page.get_by_role("button", name="Create Branch")
        self.save_button = page.get_by_role("button", name="Save")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.mobile_number = page.locator(
            'input[name="contactPostRequest.mobileNumber"]'
        )
        self.alt_mobile = page.locator(
            'input[name="contactPostRequest.alternativeMobileNumber"]'
        )
        self.whatsapp = page.locator('input[name="contactPostRequest.whatsAppNumber"]')
        self.landline = page.locator('input[name="contactPostRequest.landLineNumber"]')
        self.email = page.locator('input[name="contactPostRequest.email"]')
        self.teams_id = page.locator('input[name="contactPostRequest.teamsId"]')
        self.location_search = page.get_by_label("Search for a Location")
        self.po_box = page.locator('input[name="addressPostRequest.pOBoxNumber"]')
        self.country = page.locator('input[name="addressPostRequest.country"]')
        self.map_switch = page.locator(".MuiSwitch-root").first
        self.map_switch_input = page.locator(".MuiSwitch-input").first

    def open(self):
        """Open Branches list; reload once if Create Branch never appears."""
        self.page.get_by_role("button", name="Office Branches").click()
        self.page.get_by_role("heading", name="Branches").wait_for(
            state="visible", timeout=20_000
        )
        try:
            self.create_button.wait_for(state="visible", timeout=15_000)
        except PlaywrightTimeout:
            # Grid/API sometimes leaves the list without Create — soft reload.
            self.page.reload()
            self.page.get_by_role("heading", name="Branches").wait_for(
                state="visible", timeout=20_000
            )
            self.create_button.wait_for(state="visible", timeout=20_000)

        # Wait until Create is enabled (grid finished loading)
        expect(self.create_button).to_be_enabled(timeout=20_000)
        # Map toggle enabled is another signal the list shell has settled.
        try:
            expect(self.map_switch_input).to_be_enabled(timeout=10_000)
        except AssertionError:
            pass

    def open_create(self):
        self.create_button.click()
        self.mobile_number.wait_for(state="visible", timeout=15_000)

    def select_working_days(self, days: list[str] | None = None):
        """Select Days* is required on Create Branch."""
        days = days or DEFAULT_WORKING_DAYS
        for day in days:
            box = self.page.get_by_role("checkbox", name=day)
            box.scroll_into_view_if_needed()
            if not box.is_checked():
                # MUI checkboxes sometimes ignore .check(); click the input.
                try:
                    box.check(timeout=3_000)
                except Exception:
                    box.click(force=True)

        # Prefer 24 Hours for each selected day (avoids start/end time fills)
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
    ):
        self.mobile_number.fill(mobile)
        self.email.fill(email)
        # Landline Number* is required on Create Branch
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
        if teams_id:
            self.teams_id.fill(teams_id)
        if po_box:
            self.po_box.fill(po_box)

    def pick_location(self, query: str):
        pick_location(self.page, query, country_locator=self.country)

    def save(self, confirm: bool = True):
        self.save_button.click()
        # Confirmation dialog only appears when the form is valid
        dialog_confirm = self.page.get_by_role("button", name="Confirm")
        try:
            dialog_confirm.wait_for(state="visible", timeout=3_000)
            if confirm:
                dialog_confirm.click()
            else:
                self.page.get_by_role("button", name="Cancel").click()
        except PlaywrightTimeout:
            pass

    def reset(self):
        self.reset_button.click()

    def toggle_map_view(self):
        # Switch can stay disabled until the grid finishes loading
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
        """Read the Code column (first gridcell) from the row matching email."""
        cell = self.row_containing(email).get_by_role("gridcell").first
        expect(cell).to_be_visible(timeout=15_000)
        return (cell.inner_text() or "").strip()

    def edit_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Edit").click()
        self.mobile_number.wait_for(state="visible", timeout=15_000)

    def delete_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Delete").click()

    def confirm_dialog(self):
        self.page.get_by_role("button", name="Confirm").click()

    def cancel_dialog(self):
        self.page.get_by_role("button", name="Cancel").click()
