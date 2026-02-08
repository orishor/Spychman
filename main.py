import asyncio
import random
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 1. Load secrets from .env file
load_dotenv()
USERNAME = os.getenv("MOODLE_USER")
PASSWORD = os.getenv("MOODLE_PASS")
LOGIN_URL = os.getenv("LOGIN_URL")
TEST_URL = os.getenv("TEST_COURSE_URL")


async def human_type(page, selector, text):
    """Types text with random delays between keystrokes to mimic a human."""
    await page.focus(selector)
    for char in text:
        await page.keyboard.type(char)
        # Random delay between 50ms and 150ms
        await asyncio.sleep(random.uniform(0.05, 0.15))


async def run_poc():
    async with async_playwright() as p:
        # 2. Launch Browser (Headless=False means you SEE it happening)
        browser = await p.chromium.launch(headless=False)

        # 3. Stealth Context (Looks like a real Mac user)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("🚀 Starting PoC: Navigating to Login...")
            await page.goto(LOGIN_URL)

            # 4. Human-like Login
            # CHANGE THESE SELECTORS if RUNI uses different IDs (inspect element to check)
            await human_type(page, "#username", USERNAME)
            await asyncio.sleep(random.uniform(0.5, 1.2))

            await human_type(page, "#password", PASSWORD)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            print("🔑 Clicking Login...")
            # Wait for navigation after click
            async with page.expect_navigation():
                await page.click("#loginbtn")  # Or whatever the ID of the button is

            print("✅ Login Successful! Checking for Attendance...")

            # 5. Go to the specific class page
            await page.goto(TEST_URL)

            # 6. Look for the "Submit Attendance" link/button
            # This searches for ANY text containing 'attendance' or 'submit' (case insensitive)
            attendance_button = page.get_by_text("Submit attendance", exact=False)

            # Quick check if button exists
            if await attendance_button.is_visible():
                print("🎯 Button Found! Clicking...")
                await attendance_button.click()

                # Handling the radio button (Present/Late) if it exists
                # common in Moodle: 'status' radio button with value 'Present'
                present_radio = page.locator("input[type='radio'][value='Present']")
                if await present_radio.is_visible():
                    await present_radio.click()
                    await page.click("#id_submitbutton")  # The final 'Save changes' button

                print("🏆 Attendance Marked!")
            else:
                print("ℹ️ No attendance button active right now.")

            # Keep browser open for 5 seconds so you can see the result
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ Error: {e}")
            # Take a screenshot if it fails
            await page.screenshot(path="error_poc.png")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_poc())