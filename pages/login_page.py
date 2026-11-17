from playwright.sync_api import Page


class LoginPage:

    def __init__(self, page: Page):
        self.page = page

        # labels are real <label> elements; placeholders are empty on this page
        self.email_or_mobile = page.get_by_label("Mobile/Email ID")
        self.password = page.locator("#password")
        self.login_button = page.get_by_role("button", name="login")

    def enter_email_or_mobile(self, email_or_mobile: str):
        self.email_or_mobile.fill(email_or_mobile)

    def enter_password(self, password: str):
        self.password.fill(password)

    def click_login(self):
        self.login_button.click()

    def login(self, email_or_mobile: str, password: str):
        self.enter_email_or_mobile(email_or_mobile)
        self.enter_password(password)
        self.click_login()
