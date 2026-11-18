import re

from playwright.sync_api import Page, expect

# The suggestion row shows the full address, not the shorter text typed into the box.
SUGGESTION_TEXT = re.compile(r"Katraj,\s*Pune,\s*Maharashtra,\s*India", re.I)


def pick_location(page: Page, query: str, country_locator=None, attempts: int = 4):
    """Type a place and click the suggestion "Katraj, Pune, Maharashtra, India".

    The click happens as soon as that text is visible. Retries when Country
    stays empty after the click (common UAT flake).
    """
    search = page.get_by_label("Search for a Location")
    suggestion = page.get_by_text(SUGGESTION_TEXT)
    last_error = None

    for attempt in range(attempts):
        search.scroll_into_view_if_needed()
        search.click()
        search.fill("")
        search.press_sequentially(query, delay=30)

        suggestion.first.wait_for(state="visible", timeout=8_000)
        suggestion.first.click()

        if country_locator is None:
            return

        try:
            expect(country_locator).not_to_have_value("", timeout=10_000)
            return
        except AssertionError as err:
            last_error = err
            if attempt < attempts - 1:
                search.click()
                search.fill("")

    if last_error is not None:
        raise last_error
