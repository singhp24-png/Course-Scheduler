from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json

START_URL = "https://banner.udayton.edu/StudentRegistrationSsb/ssb/term/termSelection?mode=search"

def scrape_banner(max_pages):
    all_courses = []
    page_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        time.sleep(5)  # wait for AJAX

        while page_count < max_pages:
            page_count += 1
            print(f"Scraping page {page_count}...")

            # --- Parse current page ---
            soup = BeautifulSoup(page.content(), "html.parser")
            rows = soup.find_all("tr", attrs={"data-id": True})

            for row in rows:
                row_data = {}
                for td in row.find_all("td"):
                    if td.has_attr("data-property"):
                        row_data[td["data-property"]] = td.get_text(strip=True)
                all_courses.append(row_data)

            # --- Check for Next button ---
            next_button = page.query_selector("button.paging-control.next.enabled")
            if next_button:
                next_button.click()
                time.sleep(5)  # wait for next page to load
            else:
                print("No more pages.")
                break

    return all_courses

if __name__ == "__main__":
    courses = scrape_banner(max_pages=5)
    print(f"Total courses scraped: {len(courses)}")

    # --- Write to JSON file ---
    with open("courses.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

    print("Courses saved to courses.json")
