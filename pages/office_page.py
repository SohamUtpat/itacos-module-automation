from playwright.sync_api import Page, expect

from helpers.location import pick_location


class OfficePage:

    def __init__(self, page: Page):
        self.page = page
        self.company_name = page.locator('input[name="companyName"]')
        self.short_name = page.locator('input[name="shortName"]')
        self.payable_days = page.locator('input[name="payableDays"]')
        self.network_type = page.locator('input[name="networkType"]')
        self.currency = page.locator('input[name="currencyCode"]')
        self.mobile_number = page.locator(
            'input[name="contactPostRequest.mobileNumber"]'
        )
        self.email = page.locator('input[name="contactPostRequest.email"]')
        self.landline = page.locator('input[name="contactPostRequest.landLineNumber"]')
        self.comments = page.locator('input[name="comments"]')
        self.account_number = page.locator(
            'input[name="bankDetailsRequest.accountNumber"]'
        )
        self.iban_code = page.locator('input[name="bankDetailsRequest.ifscCode"]')
        self.bank_branch = page.locator('input[name="bankDetailsRequest.branch"]')
        self.location_search = page.get_by_label("Search for a Location")
        self.country = page.locator('input[name="addressPostRequest.country"]')
        self.address = page.locator('input[name="addressPostRequest.address"]')
        self.save_button = page.get_by_role("button", name="Save")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.view_history_button = page.get_by_role("button", name="View History").first

    def wait_until_loaded(self):
        """Wait until office form has hydrated from the API (avoids dirty-check flake)."""
        self.company_name.wait_for(state="visible", timeout=15_000)
        expect(self.company_name).not_to_have_value("", timeout=20_000)

    def open(self):
        self.page.get_by_role("button", name="Office Details").click()
        self.wait_until_loaded()

    def fill_required(
        self,
        company_name: str,
        short_name: str,
        mobile: str,
        email: str,
        location_query: str | None = None,
    ):
        self.company_name.fill(company_name)
        self.short_name.fill(short_name)
        self.mobile_number.scroll_into_view_if_needed()
        self.mobile_number.fill(mobile)
        self.email.fill(email)
        if location_query and not (self.country.input_value() or "").strip():
            self.pick_location(location_query)

    def fill_optional(self, landline: str = "", comments: str = ""):
        if landline:
            self.landline.fill(landline)
        if comments:
            self.comments.fill(comments)

    def fill_bank_details(
        self, account_number: str = "", iban_code: str = "", branch: str = ""
    ):
        self.account_number.scroll_into_view_if_needed()
        if account_number:
            self.account_number.fill(account_number)
        if iban_code:
            self.iban_code.fill(iban_code)
        if branch:
            self.bank_branch.fill(branch)

    def go_section(self, name: str):
        self.page.get_by_role("button", name=name).first.click()

    def toggle_day(self, day: str):
        box = self.page.get_by_role("checkbox", name=day).first
        box.scroll_into_view_if_needed()
        box.click()

    def open_view_history(self):
        self.view_history_button.click()
        # History may be a dialog or side panel
        history = self.page.get_by_text("History", exact=False)
        dialog = self.page.get_by_role("dialog")
        expect(history.or_(dialog).first).to_be_visible(timeout=10_000)

    def expect_history_contains(self, text: str):
        """Assert View History panel shows the given change text."""
        expect(self.page.get_by_text(text, exact=False).first).to_be_visible(
            timeout=15_000
        )

    def pick_location(self, query: str):
        pick_location(self.page, query, country_locator=self.country)

    def save(self):
        self.save_button.click()
        # Brief settle so API save / toast can finish before reload/history
        self.page.wait_for_timeout(1_500)

    def reset(self):
        self.reset_button.click()

    def reload(self):
        self.page.reload()
        self.wait_until_loaded()
