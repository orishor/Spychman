import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from main import run_process

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

KEYBOARD = [["🚀 Run Attendance Check"]]

# --- ADD THIS NEW FUNCTION ---
async def post_init(application: Application):
    """This runs automatically the second the bot starts on your computer."""
    print("📲 Pushing the button to your phone...")
    try:
        await application.bot.send_message(
            chat_id=ALLOWED_USER_ID,
            text="🤖 Spychman is online and listening. Ready when you are!",
            reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True, is_persistent=True)
        )
    except Exception as e:
        print(f"Failed to send startup message: {e}")
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text(
        "👋 Hi Ori! I am Spychman.\nPress the button below.",
        reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True, is_persistent=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ALLOWED_USER_ID:
        return

    text = update.message.text

    if text == "🚀 Run Attendance Check":
        status_msg = await update.message.reply_text("🕵️‍♂️ Checking schedule and running bot...")
        try:
            result = await run_process()
            await update.message.reply_text(f"📝 Report:\n{result['message']}")
            if result.get('screenshot'):
                with open(result['screenshot'], 'rb') as photo:
                    await update.message.reply_photo(photo=photo)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception as e:
            await update.message.reply_text(f"❌ Critical Error: {str(e)}")

def main():
    if not TOKEN or not ALLOWED_USER_ID:
        print("❌ Error: Missing credentials.")
        return

    # --- UPDATE THIS LINE TO INCLUDE post_init ---
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram Bot is running... (Press Ctrl+C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()