import requests
import pytz
from ics import Calendar
from datetime import datetime
from config import ICS_URL, COURSE_MAPPING


def get_current_moodle_id():
    """
    Fetches schedule and returns the Moodle ID, False (Ignore), or None (Unknown).
    """
    print("📅 Checking Schedule...")

    try:
        # 1. Fetch ICS
        response = requests.get(ICS_URL)
        response.encoding = 'utf-8'
        c = Calendar(response.text)

        # 2. Get Current Time (Israel)
        israel_tz = pytz.timezone('Asia/Jerusalem')
        now = datetime.now(israel_tz)
        print(f"🕒 Time: {now.strftime('%H:%M')}")

        # 3. Find Active Event
        current_event = None
        for event in c.events:
            if event.begin <= now <= event.end:
                current_event = event
                break

        if not current_event:
            print("❌ No class is currently happening.")
            return None

        event_name = current_event.name
        print(f"🎓 Current Class: '{event_name}'")

        # 4. Fuzzy Match against Dictionary (Longest Match Wins)
        best_id = None
        longest_match = 0

        for key, val in COURSE_MAPPING.items():
            if key in event_name:
                if len(key) > longest_match:
                    longest_match = len(key)
                    best_id = val

        if best_id:
            return best_id
        elif best_id is False:
            print(f"🛑 Class '{event_name}' is in your Ignore List. Skipping.")
            return False
        else:
            print(f"⚠️ WARNING: Class '{event_name}' found, but not in COURSE_MAPPING.")
            return None

    except Exception as e:
        print(f"❌ Error fetching schedule: {e}")
        return None