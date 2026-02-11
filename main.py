import asyncio
from scheduler import get_current_moodle_id
from state import has_already_marked
from bot import run_attendance_bot


async def main():
    # 1. Get ID from Schedule
    moodle_id = get_current_moodle_id()

    if moodle_id:
        # 2. Check History (Don't run if already done today)
        if has_already_marked(moodle_id):
            print(f"🛑 Skipping: Attendance for ID {moodle_id} was already marked today.")
        else:
            # 3. Run Bot
            print(f"🚦 Starting Bot for ID: {moodle_id}")
            await run_attendance_bot(moodle_id)

    elif moodle_id is False:
        print("💤 Class found but marked as 'Ignore' in config.")

    else:
        print("💤 No active class or unknown class detected.")


if __name__ == "__main__":
    asyncio.run(main())