from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect


class UnitsPage:

    def __init__(self, page: Page):
        self.page = page
        self.create_button = page.get_by_role("button", name="Create Unit")
        self.submit_button = page.get_by_role("button", name="Submit")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.search = page.get_by_placeholder("Search here")
        self.first_name = page.locator('input[name="firstName"]')
        self.last_name = page.locator('input[name="lastName"]')
        self.email = page.locator('input[name="email"]')
        self.phone = page.locator('input[name="phone"]')
        self.password = page.locator('input[name="password"]')
        self.confirm_password = page.locator('input[name="confirmPassword"]')
        self.country_code_select = page.locator("#mui-component-select-countryCode")
        self.branch_select = page.locator("#mui-component-select-branchId")
        self.language_select = page.locator("#languageCode-selection")
        self.back_button = page.locator("[data-testid='ArrowBackIcon']")
        self.map_switch = page.locator(".MuiSwitch-root").first
        self.map_switch_input = page.locator(".MuiSwitch-input").first

    def open(self):
        self.page.get_by_role("button", name="Units").click()
        self.page.get_by_role("heading", name="Units").wait_for(
            state="visible", timeout=20_000
        )
        self.create_button.wait_for(state="visible", timeout=20_000)

    def open_create(self):
        self.create_button.click()
        self.first_name.wait_for(state="visible", timeout=15_000)

    def select_country_code(self, option_text: str = "India"):
        """Pick country dial code. Default UI is often already +91 for India."""
        current = (self.country_code_select.inner_text() or "").strip()
        # Options are dial codes (+91), not country names — skip if already set.
        if option_text in ("India", "+91") and "+91" in current:
            return
        if option_text and option_text in current:
            return

        self.country_code_select.click()
        listbox = self.page.get_by_role("listbox")
        listbox.wait_for(state="visible", timeout=5_000)

        # Prefer dial-code match; fall back to label text, then first option.
        option = listbox.locator('[data-value="+91"]')
        if option_text not in ("India", "+91"):
            option = listbox.get_by_role("option").filter(has_text=option_text)
            if option.count() == 0:
                option = listbox.locator(f'[data-value="{option_text}"]')
        if option.count() == 0:
            option = listbox.get_by_role("option").first

        option.first.wait_for(state="visible", timeout=5_000)
        option.first.click()
        listbox.wait_for(state="hidden", timeout=5_000)

    def select_branch(self, branch_code: str):
        self.branch_select.click()
        self.page.get_by_role("option", name=branch_code).click()

    def select_language(self, name: str = "English"):
        """Select a Language option on Other Details (e.g. English)."""
        self.language_select.wait_for(state="visible", timeout=10_000)
        self.language_select.click()
        option = self.page.get_by_role("option", name=name)
        option.wait_for(state="visible", timeout=5_000)
        option.click()

    def back(self):
        """Leave the form. After create, this returns to the units list."""
        self.back_button.click()

    def fill_required(
        self,
        first_name: str,
        email: str,
        phone: str,
        password: str,
        confirm_password: str | None = None,
        branch_code: str | None = None,
        last_name: str = "",
        country_code: str = "India",
    ):
        if first_name:
            self.first_name.fill(first_name)
        if last_name:
            self.last_name.fill(last_name)
        if email:
            self.email.fill(email)
        if self.country_code_select.is_visible():
            self.select_country_code(country_code)
        if phone:
            self.phone.fill(phone)
        if password:
            self.password.fill(password)
        confirm = confirm_password if confirm_password is not None else password
        if confirm:
            self.confirm_password.fill(confirm)
        if branch_code:
            self.select_branch(branch_code)

    def fill_all(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        password: str,
        branch_code: str,
        country_code: str = "India",
    ):
        self.fill_required(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password=password,
            branch_code=branch_code,
            country_code=country_code,
        )

    def finish_create(self):
        """Submit Personal Details, then go back to the units list.

        That first Submit creates the unit. Other Details is a later update,
        so Back is enough to see the new row.
        """
        self.submit_button.click()
        self.page.get_by_text("user created successfully", exact=True).first.wait_for(
            state="visible", timeout=15_000
        )
        self.page.get_by_role("heading", name="Other Details").wait_for(
            state="visible", timeout=15_000
        )
        self.back()

    def submit(self):
        self.submit_button.click()

    def save_edit(self):
        """Submit the edit form. Other Details may open with Submit disabled."""
        self.submit_button.click()
        try:
            self.page.get_by_role("heading", name="Other Details").wait_for(
                state="visible", timeout=5_000
            )
        except PlaywrightTimeout:
            return

        if not self.submit_button.is_enabled():
            self.select_language("English")
        if self.submit_button.is_enabled():
            self.submit_button.click()
            return
        self.back()

    def reset(self):
        self.reset_button.click()

    def search_for(self, text: str):
        self.search.fill(text)

    def clear_search(self):
        self.search.fill("")

    def toggle_map_view(self):
        expect(self.map_switch_input).to_be_enabled(timeout=20_000)
        self.page.get_by_text("Map view").locator("..").locator(
            ".MuiSwitch-root"
        ).click()

    def row_by_email(self, email: str):
        return self.page.get_by_role("gridcell", name=email)

    def row_containing(self, email: str):
        return self.page.locator(f"[role='row']:has-text('{email}')")

    def edit_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Edit").click()
        self.first_name.wait_for(state="visible", timeout=15_000)

    def delete_row_by_email(self, email: str):
        self.row_containing(email).get_by_role("menuitem", name="Delete").click()

    def confirm_dialog(self):
        self.page.get_by_role("button", name="Confirm").click()

    def cancel_dialog(self):
        self.page.get_by_role("button", name="Cancel").click()
