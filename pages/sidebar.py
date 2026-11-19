from playwright.sync_api import Page


class Sidebar:

    def __init__(self, page: Page):
        self.page = page

    def go_dashboard(self):
        self.page.get_by_role("button", name="Dashboard").click()

    def go_office_details(self):
        self.page.get_by_role("button", name="Office Details").click()

    def go_office_branches(self):
        self.page.get_by_role("button", name="Office Branches").click()

    def go_units(self):
        self.page.get_by_role("button", name="Units").click()

    def go_workshops(self):
        self.page.get_by_role("button", name="Workshops", exact=True).click()
