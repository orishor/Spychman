import json
import os
from datetime import datetime
from config import LOG_FILE


def has_already_marked(course_id):
    """Checks if we already marked this course ID today."""
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(LOG_FILE):
        return False

    try:
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
            # Check if today's date exists AND if this course is in today's list
            if today in log and course_id in log[today]:
                return True
    except:
        return False
    return False


def save_successful_mark(course_id):
    """Saves this course ID to today's log."""
    today = datetime.now().strftime("%Y-%m-%d")
    data = {}

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}

    if today not in data:
        data[today] = []

    if course_id not in data[today]:
        data[today].append(course_id)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"📝 Logged success for ID {course_id} on {today}.")