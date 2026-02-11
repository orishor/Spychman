import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
USERNAME = os.getenv("MOODLE_USER")
PASSWORD = os.getenv("MOODLE_PASS")

# URLs
ICS_URL = "https://yedion.runi.ac.il/yedion/fireflyweb.aspx?prgname=PublicHours&Google_InnerID=8487384048324&Google_Token=3a707b90-f4bb-93f0-58d2-3caef92616e6-08d62fd2-2c84&Google_Population=S"
LOG_FILE = "attendance_log.json"

# Course Mappings
COURSE_MAPPING = {
    # Active Courses
    "רפואה בקהילה": "49909",
    "מבוא לפרמקולוגיה": "73992",
    "פתולוגיה כללית": "50895",
    "אנטומיה חזה בטן אגן וגפיים": "41318",
    "מבוא לאפידימיולוגיה": "49733",
    "רופא אדם חברה שנה א׳": "46260",
    "רופא אדם חברה": "46260",

    # Aliases
    "פתולוגיה קלינית": "50895",

    # Ignored
    "שבוע היכרות": False,
    "ללמוד איך ללמוד": False,
    "אנטומיה פונקציונלית": False,
    "פרוייקט עבודת גמר": False,
    "English Exemption": False,
}