from playwright.sync_api import sync_playwright
import os

COLONNINA = os.environ["COLONNINA_NAME"]
TARGA = os.environ["LICENSE_PLATE"]

URL = "https://nea.wrt.stellantis.com/parking/#/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)

    page.get_by_text(COLONNINA).scroll_into_view_if_needed()
    page.locator(
        f"xpath=//*[contains(., '{COLONNINA}')]//button[contains(., 'Prenota')]"
    ).click()

    page.locator("input[type='checkbox'], input[type='radio']").first.check()
    page.get_by_role("button", name="NEXT").click()

    page.locator("input, textarea").first.fill(TARGA)
    page.get_by_role("button", name="Salva").click()

    browser.close()
