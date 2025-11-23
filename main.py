from playwright.sync_api import sync_playwright
import json
from collections import defaultdict

START_URL = "https://banner.udayton.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"

def parse_class_row(row):
    """Extract course data from a table row using data-property attributes."""
    data = {}
    tds = row.locator("td").all()
    for td in tds:
        prop = td.get_attribute("data-property")
        if prop:
            data[prop] = td.inner_text().strip()
    return data

def scrape_banner():
    courses = defaultdict(lambda: {"meetings": []})  # group by CRN

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(START_URL)

        # --- Term selection ---
        page.wait_for_selector(".select2-chosen")
        page.click(".select2-chosen")
        page.fill(".select2-input", "Spring 2026")
        page.locator("div.select2-result-label", has_text="Spring 2026").click()
        page.locator("button#term-go").click(force=True)

        # --- Click Search ---
        page.wait_for_selector("button#search-go")
        page.locator("button#search-go").click()
        page.wait_for_selector("table#searchResults tbody tr")

        # --- Scrape pages ---
        while True:
            rows = page.locator("table#searchResults tbody tr").all()
            for row in rows:
                data = parse_class_row(row)
                crn = data.get("crn")
                if not crn:
                    continue

                # Store main course info if not already present
                if not courses[crn].get("subject"):
                    for key, value in data.items():
                        if key not in ["meetingDays", "meetingTime", "building", "room"]:
                            courses[crn][key] = value

                # Store meeting info
                meeting = {k: data[k] for k in ["meetingDays", "meetingTime", "building", "room"] if k in data}
                if meeting:
                    courses[crn]["meetings"].append(meeting)

            next_btn = page.locator("button[aria-label='Next Page']")
            if next_btn.is_disabled():
                break

            next_btn.click()
            page.wait_for_selector("table#searchResults tbody tr")  # wait for next page

        browser.close()

    return list(courses.values())

if __name__ == "__main__":
    data = scrape_banner()
    with open("classes.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Saved classes.json")
