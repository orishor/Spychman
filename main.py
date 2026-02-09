import asyncio
import random
import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 1. Load secrets
load_dotenv()
USERNAME = os.getenv("MOODLE_USER")
PASSWORD = os.getenv("MOODLE_PASS")
ATTENDANCE_URL = "https://moodle.runi.ac.il/2026/mod/attendance/view.php?id=49909"


async def human_type(page, selector, text):
    """Types text with random delays."""
    if isinstance(selector, str):
        await page.focus(selector)
    else:
        await selector.focus()

    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.1))


async def take_screenshot(page, status_label):
    """Helper to take a timestamped screenshot."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"moodle_{status_label}_{timestamp}.png"
    await page.screenshot(path=filename, full_page=True)
    print(f"📸 Screenshot saved: {filename}")


async def run_bot():
    async with async_playwright() as p:
        # headless=False so you can see it working
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🚀 Navigating to Attendance: {ATTENDANCE_URL}")
            await page.goto(ATTENDANCE_URL)

            # --- LOGIN HANDLING ---
            # 1. Check for "Hangup" page
            try:
                hangup_btn = page.get_by_text("לחץ כאן להמשך")
                if await hangup_btn.is_visible(timeout=3000):
                    print("⚠️ Clicked 'Hangup' continue button.")
                    await hangup_btn.click()
            except:
                pass

            # 2. Check for Login Form
            if await page.locator("input[type='password']").is_visible(timeout=5000):
                print("🔒 Login required. Entering credentials...")

                # Username
                user_input = page.get_by_placeholder("שם משתמש")
                if not await user_input.is_visible(): user_input = page.get_by_placeholder("User Name")
                if not await user_input.is_visible(): user_input = page.locator("input[type='text']").first
                await human_type(page, user_input, USERNAME)

                # Password
                pass_input = page.get_by_placeholder("סיסמה")
                if not await pass_input.is_visible(): pass_input = page.get_by_placeholder("Password")
                if not await pass_input.is_visible(): pass_input = page.locator("input[type='password']").first
                await human_type(page, pass_input, PASSWORD)

                # Click Login
                login_btn = page.get_by_role("button", name="התחבר")
                if not await login_btn.is_visible(): login_btn = page.get_by_role("button", name="Log on")
                await login_btn.click()
                await page.wait_for_load_state("networkidle")

            # --- ATTENDANCE HANDLING ---
            print("👀 Looking for 'Submit attendance' button...")

            # We look for the button, but we don't crash if it's missing
            submit_link = page.get_by_text("Submit attendance", exact=False).or_(page.get_by_text("הגשת נוכחות"))

            if await submit_link.is_visible():
                print("🎯 Button FOUND! Clicking...")
                await submit_link.click()

                # Select "Present"
                present_radio = page.get_by_label("Present").or_(page.get_by_label("נוכח/ת"))
                if not await present_radio.is_visible():
                    present_radio = page.locator("input[type='radio']").first

                if await present_radio.is_visible():
                    await present_radio.click()

                    # Save
                    save_btn = page.get_by_role("button", name="Save changes").or_(
                        page.get_by_role("button", name="שמירת שינויים"))
                    await save_btn.click()
                    print("✅ Attendance marked successfully.")

                    # SUCCESS SCREENSHOT
                    await take_screenshot(page, "SUCCESS")
                else:
                    print("❌ Found submit page, but no 'Present' option.")
                    await take_screenshot(page, "ERROR_NO_RADIO")

            else:
                print("ℹ️ Button NOT found. (Class likely not started).")
                # FAIL/DEBUG SCREENSHOT
                # This helps you see exactly what the bot sees when it fails
                await take_screenshot(page, "DEBUG_NO_BUTTON")

        except Exception as e:
            print(f"❌ Script Error: {e}")
            await take_screenshot(page, "CRITICAL_ERROR")

        finally:
            print("👋 Closing browser.")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_bot())