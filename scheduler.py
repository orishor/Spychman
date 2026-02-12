import requests
import pytz
from ics import Calendar
from datetime import datetime, timedelta
from config import ICS_URL, COURSE_MAPPING


def get_current_moodle_id():
    """
    Fetches schedule and returns the Moodle ID, False (Ignore), or None (Unknown).
    Looks for classes currently happening OR starting within the next 20 minutes.
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

        # Calculate lookahead window (Now + 20 mins)
        lookahead = timedelta(minutes=20)
        future_window = now + lookahead

        print(f"🕒 Time: {now.strftime('%H:%M')} (Looking ahead to {future_window.strftime('%H:%M')})")

        # 3. Find Active or Upcoming Event
        current_event = None
        for event in c.events:
            # Check A: Is class happening NOW?
            if event.begin <= now <= event.end:
                current_event = event
                print("✅ Found active class.")
                break

            # Check B: Is class starting SOON (within 20 mins)?
            if now <= event.begin <= future_window:
                current_event = event
                print(f"⏰ Found upcoming class starting at {event.begin.strftime('%H:%M')}")
                break

        if not current_event:
            print("❌ No class active or starting in 20 mins.")
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