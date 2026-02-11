import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
from config import USERNAME, PASSWORD
from state import save_successful_mark


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


async def run_attendance_bot(moodle_id):
    attendance_url = f"https://moodle.runi.ac.il/2026/mod/attendance/view.php?id={moodle_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🚀 Navigating to Attendance URL: {attendance_url}")
            await page.goto(attendance_url)

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

                user_input = page.get_by_placeholder("שם משתמש")
                if not await user_input.is_visible(): user_input = page.get_by_placeholder("User Name")
                if not await user_input.is_visible(): user_input = page.locator("input[type='text']").first
                await human_type(page, user_input, USERNAME)

                pass_input = page.get_by_placeholder("סיסמה")
                if not await pass_input.is_visible(): pass_input = page.get_by_placeholder("Password")
                if not await pass_input.is_visible(): pass_input = page.locator("input[type='password']").first
                await human_type(page, pass_input, PASSWORD)

                login_btn = page.get_by_role("button", name="כניסה")
                if not await login_btn.is_visible(): login_btn = page.get_by_role("button", name="Log on")
                if not await login_btn.is_visible(): login_btn = page.get_by_role("button", name="התחבר")

                await login_btn.click()
                await page.wait_for_load_state("networkidle")

            # --- ATTENDANCE HANDLING ---
            print("👀 Looking for 'Submit attendance' button...")

            submit_link = page.get_by_text("Submit attendance", exact=False).or_(page.get_by_text("עדכון נוכחות")).or_(
                page.get_by_text("הגשת נוכחות"))

            if await submit_link.is_visible():
                print("🎯 Button FOUND! Clicking...")
                await submit_link.click()

                present_radio = page.get_by_label("Present").or_(page.get_by_label("נוכח/ת"))
                if not await present_radio.is_visible():
                    present_radio = page.locator("input[type='radio']").first

                if await present_radio.is_visible():
                    await present_radio.click()

                    save_btn = page.get_by_role("button", name="Save changes").or_(
                        page.get_by_role("button", name="שמירת שינויים"))
                    await save_btn.click()
                    print("✅ Attendance marked successfully.")

                    # Save to local log to prevent re-run today
                    save_successful_mark(moodle_id)

                    await take_screenshot(page, "SUCCESS")
                else:
                    print("❌ Found submit page, but no 'Present' option.")
                    await take_screenshot(page, "ERROR_NO_RADIO")

            else:
                print("ℹ️ Button NOT found. (Class likely not started).")
                await take_screenshot(page, "DEBUG_NO_BUTTON")

        except Exception as e:
            print(f"❌ Script Error: {e}")
            await take_screenshot(page, "CRITICAL_ERROR")

        finally:
            print("👋 Closing browser.")
            await browser.close()