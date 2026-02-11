import asyncio
from scheduler import get_current_moodle_id
from state import has_already_marked
from bot import run_attendance_bot


async def run_process():
    """
    The Core Logic.
    Used by BOTH the Telegram Bot and Manual Terminal runs.
    Returns: dict { 'status': str, 'message': str, 'screenshot': str|None }
    """
    # 1. Get ID from Schedule
    moodle_id = get_current_moodle_id()

    if moodle_id:
        # 2. Check History
        if has_already_marked(moodle_id):
            return {
                "status": "skipped",
                "message": f"🛑 **Skipped:** Attendance for ID `{moodle_id}` was already marked today.",
                "screenshot": None
            }
        else:
            # 3. Run Bot (Returns the report dict directly)
            print(f"🚦 Starting Bot for ID: {moodle_id}")
            return await run_attendance_bot(moodle_id)

    elif moodle_id is False:
        return {
            "status": "ignored",
            "message": "💤 Class found, but it is on your **Ignore List**.",
            "screenshot": None
        }

    else:
        return {
            "status": "idle",
            "message": "💤 No active class found in the schedule right now.",
            "screenshot": None
        }


if __name__ == "__main__":
    # --- MANUAL MODE ---
    # This runs when you type 'python main.py' in your terminal
    print("--- 🖐️ MANUAL RUN STARTED ---")

    result = asyncio.run(run_process())

    print("\n" + "=" * 30)
    print(f"STATUS:  {result['status'].upper()}")
    print(f"MESSAGE: {result['message']}")

    if result['screenshot']:
        print(f"EVIDENCE: {result['screenshot']}")
        # On Mac, this command opens the screenshot automatically:
        import subprocess

        try:
            subprocess.run(["open", result['screenshot']])
        except:
            pass

    print("=" * 30 + "\n")