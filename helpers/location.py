import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect


def pick_location(page: Page, query: str, country_locator=None, attempts: int = 4):
    """Type into Search for a Location and choose a Google Places suggestion.

    Retries when autocomplete is slow or Country stays empty (common UAT flake).
    """
    search = page.get_by_label("Search for a Location")
    place = query.split(",")[0].strip()
    pac_items = page.locator(".pac-item")
    last_error = None

    for attempt in range(attempts):
        search.scroll_into_view_if_needed()
        search.click()
        # Fully clear so Places re-fetches suggestions.
        search.fill("")
        search.press("Control+A")
        search.press("Backspace")
        page.wait_for_timeout(200)

        search.press_sequentially(query, delay=120)
        # Give Places time to return suggestions before clicking.
        page.wait_for_timeout(800 + attempt * 400)

        selected = False
        try:
            pac_items.first.wait_for(state="visible", timeout=8_000)
            pac_items.first.click()
            selected = True
        except (PlaywrightTimeout, Exception):
            candidates = [
                page.locator(".MuiAutocomplete-option").first,
                page.get_by_role("option").first,
                page.get_by_text(re.compile(r"Katraj.*Pune.*India", re.I)).first,
                page.get_by_text(re.compile(re.escape(place), re.I)).nth(1),
            ]
            for locator in candidates:
                try:
                    locator.wait_for(state="visible", timeout=3_000)
                    locator.click()
                    selected = True
                    break
                except (PlaywrightTimeout, Exception):
                    continue

        if not selected:
            page.wait_for_timeout(1_500)
            search.press("ArrowDown")
            search.press("Enter")

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
                page.wait_for_timeout(500)

    if last_error is not None:
        raise last_error
