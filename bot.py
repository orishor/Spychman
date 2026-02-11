import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
from config import USERNAME, PASSWORD
from state import save_successful_mark


# --- HELPER FUNCTIONS ---

async def random_sleep(min_seconds=1.0, max_seconds=3.0):
    """Sleeps for a random amount of time to mimic human thinking."""
    ms = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(ms)


async def human_type(page, selector, text):
    """Types text with random delays."""
    if isinstance(selector, str):
        await page.focus(selector)
    else:
        await selector.focus()

    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.1, 0.3))
    await random_sleep(0.5, 1.5)


async def human_click(page, selector):
    """Moves mouse to element, hovers, then clicks with delay."""
    if isinstance(selector, str):
        loc = page.locator(selector)
    else:
        loc = selector

    # 1. Hover first (visual cue)
    await loc.hover()

    # 2. Hesitate
    await asyncio.sleep(random.uniform(0.2, 0.7))

    # 3. Click
    await loc.click()

    # 4. React
    await random_sleep(1.0, 2.0)


async def take_screenshot(page, status_label):
    """Takes a screenshot and RETURNS the filename."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"moodle_{status_label}_{timestamp}.png"
    await page.screenshot(path=filename, full_page=True)
    print(f"📸 Screenshot saved: {filename}")
    return filename


# --- MAIN LOGIC ---

async def run_attendance_bot(moodle_id):
    """
    Runs the browser automation.
    RETURNS: A dictionary { 'status': str, 'message': str, 'screenshot': str|None }
    """
    attendance_url = f"https://moodle.runi.ac.il/2026/mod/attendance/view.php?id={moodle_id}"

    # Default return state (Error)
    result_report = {
        "status": "error",
        "message": "❌ Unknown error occurred.",
        "screenshot": None
    }

    async with async_playwright() as p:
        # headless=False lets you watch it (Manual Mode)
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🚀 Navigating to: {attendance_url}")
            await page.goto(attendance_url)
            await random_sleep(2.0, 4.0)

            # --- LOGIN HANDLING ---
            try:
                hangup_btn = page.get_by_text("לחץ כאן להמשך")
                if await hangup_btn.is_visible(timeout=3000):
                    print("⚠️ Clicked 'Hangup' continue button.")
                    await human_click(page, hangup_btn)
            except:
                pass

            if await page.locator("input[type='password']").is_visible(timeout=5000):
                print("🔒 Login required...")

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

                await human_click(page, login_btn)
                await page.wait_for_load_state("networkidle")

            # --- ATTENDANCE HANDLING ---
            print("👀 Looking for 'Submit attendance' button...")
            await random_sleep(1.5, 3.0)

            submit_link = page.get_by_text("Submit attendance", exact=False).or_(page.get_by_text("עדכון נוכחות")).or_(
                page.get_by_text("הגשת נוכחות"))

            if await submit_link.is_visible():
                print("🎯 Button FOUND! Clicking...")
                await human_click(page, submit_link)

                present_radio = page.get_by_label("Present").or_(page.get_by_label("נוכח/ת"))
                if not await present_radio.is_visible():
                    present_radio = page.locator("input[type='radio']").first

                if await present_radio.is_visible():
                    print("✅ Selecting 'Present'...")
                    await human_click(page, present_radio)

                    save_btn = page.get_by_role("button", name="Save changes").or_(
                        page.get_by_role("button", name="שמירת שינויים"))
                    await human_click(page, save_btn)

                    print("🏆 Attendance marked successfully.")

                    # Log to JSON
                    save_successful_mark(moodle_id)

                    # Capture Success Screenshot
                    shot_path = await take_screenshot(page, "SUCCESS")

                    # Success Result
                    result_report = {
                        "status": "success",
                        "message": f"✅ Successfully marked attendance for ID {moodle_id}.",
                        "screenshot": shot_path
                    }
                else:
                    print("❌ Error: No radio button found.")
                    shot_path = await take_screenshot(page, "ERROR_NO_RADIO")
                    result_report = {
                        "status": "error",
                        "message": "❌ 'Submit' clicked, but 'Present' option not found.",
                        "screenshot": shot_path
                    }

            else:
                print("ℹ️ Button NOT found.")
                shot_path = await take_screenshot(page, "DEBUG_NO_BUTTON")
                result_report = {
                    "status": "skipped",
                    "message": "ℹ️ 'Submit Attendance' button not found (Class likely not started).",
                    "screenshot": shot_path
                }

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            try:
                shot_path = await take_screenshot(page, "CRITICAL_ERROR")
            except:
                shot_path = None

            result_report = {
                "status": "error",
                "message": f"❌ Critical Script Error: {str(e)}",
                "screenshot": shot_path
            }

        finally:
            print("👋 Closing browser.")
            await browser.close()

            # RETURN the report so main.py or telegram_bot.py can use it
            return result_report