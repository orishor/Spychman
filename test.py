from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        # 1. headless=False -> Visible browser
        # 2. slow_mo=1000 -> Wait 1 second between every action
        print("Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()

        print("Navigating to Google...")
        page.goto("https://www.google.com")

        print("Typing hello...")
        page.fill("textarea[name='q']", "Hello World")

        print("Closing in 5 seconds...")
        page.wait_for_timeout(5000)
        browser.close()


if __name__ == "__main__":
    run()