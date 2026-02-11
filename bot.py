import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
from config import USERNAME, PASSWORD
from state import save_successful_mark


async def random_sleep(min_seconds=1.0, max_seconds=3.0):
    """Sleeps for a random amount of time to mimic human thinking/reading."""
    ms = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(ms)


async def human_type(page, selector, text):
    """Types text with random delays (slower variance)."""
    if isinstance(selector, str):
        await page.focus(selector)
    else:
        await selector.focus()

    for char in text:
        await page.keyboard.type(char)
        # Slower typing: 0.1s to 0.3s per key
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Pause after typing a field (like a human checking their input)
    await random_sleep(0.5, 1.5)


async def human_click(page, selector):
    """Moves mouse to element, hovers briefly, then clicks with delay."""
    # If selector is a Locator object, use it directly; otherwise create one
    if isinstance(selector, str):
        loc = page.locator(selector)
    else:
        loc = selector

    # 1. Hover first (visual cue of mouse movement)
    await loc.hover()

    # 2. Small hesitation before clicking
    await asyncio.sleep(random.uniform(0.2, 0.7))

    # 3. Click
    await loc.click()

    # 4. Post-click pause (reaction time)
    await random_sleep(1.0, 2.0)


async def take_screenshot(page, status_label):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"moodle_{status_label}_{timestamp}.png"
    await page.screenshot(path=filename, full_page=True)
    print(f"📸 Screenshot saved: {filename}")


async def run_attendance_bot(moodle_id):
    attendance_url = f"https://moodle.runi.ac.il/2026/mod/attendance/view.php?id={moodle_id}"

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print(f"🚀 Navigating to Attendance URL: {attendance_url}")
            await page.goto(attendance_url)
            await random_sleep(2.0, 4.0)  # Wait for page to fully settle

            # --- LOGIN HANDLING ---
            try:
                hangup_btn = page.get_by_text("לחץ כאן להמשך")
                if await hangup_btn.is_visible(timeout=3000):
                    print("⚠️ Clicked 'Hangup' continue button.")
                    await human_click(page, hangup_btn)
            except:
                pass

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

                await human_click(page, login_btn)
                await page.wait_for_load_state("networkidle")

            # --- ATTENDANCE HANDLING ---
            print("👀 Looking for 'Submit attendance' button...")

            # Add a "thinking" pause before clicking submit
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