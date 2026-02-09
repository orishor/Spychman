import asyncio
import random
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 1. Load secrets from .env file
load_dotenv()
USERNAME = os.getenv("MOODLE_USER")
PASSWORD = os.getenv("MOODLE_PASS")
# We use the specific attendance URL as the entry point
ATTENDANCE_URL = "https://moodle.runi.ac.il/2026/mod/attendance/view.php?id=49909"


async def human_type(page, selector, text):
    """Types text with random delays to mimic human input."""
    # check if selector is a string or a locator
    if isinstance(selector, str):
        await page.focus(selector)
    else:
        await selector.focus()

    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))


async def run_poc():
    async with async_playwright() as p:
        # Launch browser (headless=False so you can watch it work)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🚀 Starting: Navigating directly to Attendance Page ({ATTENDANCE_URL})...")
            await page.goto(ATTENDANCE_URL)

            # --- PHASE 1: HANDLE LOGIN GATES (If redirected) ---

            # Check A: The 'Hangup' / 'Click to continue' intermediate page
            # We wait briefly to see if this specific text appears
            try:
                hangup_btn = page.get_by_text("לחץ כאן להמשך")
                if await hangup_btn.is_visible(timeout=3000):
                    print("⚠️ Found 'Hangup' page. Clicking continue...")
                    await hangup_btn.click()
            except:
                pass  # Continue if not found

            # Check B: The Login Page (my.policy)
            # We check if a password field is visible.
            password_field = page.locator("input[type='password']")
            if await password_field.is_visible(timeout=5000):
                print("🔒 Login page detected. Entering credentials...")

                # Using 'get_by_placeholder' is often more robust than IDs for these forms
                # Try Hebrew placeholders first, then English, or fallback to generic types

                # Fill Username
                user_input = page.get_by_placeholder("שם משתמש")
                if not await user_input.is_visible():
                    user_input = page.get_by_placeholder("User Name")
                if not await user_input.is_visible():
                    user_input = page.locator("input[type='text']").first

                await human_type(page, user_input, USERNAME)

                # Fill Password
                pass_input = page.get_by_placeholder("סיסמה")
                if not await pass_input.is_visible():
                    pass_input = page.get_by_placeholder("Password")
                if not await pass_input.is_visible():
                    pass_input = password_field

                await human_type(page, pass_input, PASSWORD)

                print("🔑 Clicking Login...")
                # Click the button (usually "התחבר" or "Log on")
                login_btn = page.get_by_role("button", name="התחבר")
                if not await login_btn.is_visible():
                    login_btn = page.get_by_role("button", name="Log on")

                await login_btn.click()

                # Wait for the redirect back to Moodle
                await page.wait_for_load_state("networkidle")

            # --- PHASE 2: MARK ATTENDANCE ---

            print("Checking for 'Submit Attendance' button...")

            # Verify we are on the right page
            if "mod/attendance/view.php" not in page.url:
                print(f"⚠️ Warning: Current URL is {page.url}, expected attendance view.")

            # Look for the link. It might be "Submit attendance" (English) or "הגשת נוכחות" (Hebrew)
            # We use a regex to match either case insensitive.
            submit_link = page.get_by_text("Submit attendance", exact=False).or_(page.get_by_text("הגשת נוכחות"))

            if await submit_link.is_visible():
                print("🎯 'Submit' link found! Clicking...")
                await submit_link.click()

                # Now we are on the form page. We need to select "Present".
                # Moodle usually has radio buttons: Present (P), Late (L), Excused (E), Absent (A).
                # The "Present" button is often the first one or has value="Present" / status description containing "Present"/"נוכח".

                print("Looking for 'Present' status...")

                # Try to find the radio button by its label text "Present" or "נוכח"
                present_radio = page.get_by_label("Present").or_(page.get_by_label("נוכח/ת"))

                # Fallback: look for the first radio button if specific label fails (risky but often works)
                if not await present_radio.is_visible():
                    present_radio = page.locator("input[type='radio']").first

                if await present_radio.is_visible():
                    await present_radio.click()
                    print("✅ Selected 'Present'.")

                    # Click "Save changes" / "שמירת שינויים"
                    save_btn = page.get_by_role("button", name="Save changes").or_(
                        page.get_by_role("button", name="שמירת שינויים"))
                    await save_btn.click()
                    print("🏆 Attendance Saved Successfully!")
                else:
                    print("❌ Could not find the 'Present' radio button options.")
            else:
                print("ℹ️ 'Submit attendance' link is NOT visible. (Class might not be open yet?)")

            # Keep browser open briefly
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="error_debug.png")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_poc())