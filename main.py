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
                print("🔒 Login