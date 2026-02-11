import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import the core logic from main.py
from main import run_process

# Setup logging (optional, good for debugging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Ensure we cast the ID to integer for comparison
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# The Button Layout
KEYBOARD = [["🚀 Run Attendance Check"]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the welcome message with the button."""
    user = update.effective_user
    if user.id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Access Denied.")
        return

    await update.message.reply_text(
        "👋 Hi Ori! I am Spychman.\nPress the button below to check for class.",
        reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the button press."""
    user = update.effective_user
    if user.id != ALLOWED_USER_ID:
        return

    text = update.message.text

    if text == "🚀 Run Attendance Check":
        status_msg = await update.message.reply_text("🕵️‍♂️ Checking schedule and running bot...")

        try:
            # --- CALL MAIN.PY ---
            result = await run_process()

            # 1. Send Text Report
            await update.message.reply_text(f"📝 Report:\n{result['message']}")

            # 2. Send Screenshot (if exists)
            if result.get('screenshot'):
                with open(result['screenshot'], 'rb') as photo:
                    await update.message.reply_photo(photo=photo)

            # Delete the "Checking..." message to keep chat clean
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)

        except Exception as e:
            await update.message.reply_text(f"❌ Critical Error: {str(e)}")


def main():
    """Start the bot."""
    if not TOKEN or not ALLOWED_USER_ID:
        print("❌ Error: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing in .env")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram Bot is running... (Press Ctrl+C to stop)")
    app.run_polling()


if __name__ == "__main__":
    main()