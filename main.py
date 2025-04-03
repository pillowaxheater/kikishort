import logging
import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from openai import OpenAI

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_key")
openai.api_key = OPENAI_API_KEY  # Set key in old-style way

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Global variables to store all messages
all_messages = []

# Store messages per chat
messages = {}
last_requests = {}

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save incoming messages."""
    if not update.message or not update.message.text:  # Ignore updates that don't have text messages
        return

    chat_id = update.effective_chat.id
    user = update.message.from_user.first_name
    text = update.message.text
    timestamp = datetime.datetime.now()

    # Initialize chat history if it doesn't exist
    if chat_id not in messages:
        messages[chat_id] = []

    # Don't save the "короче" command itself
    if text.lower() != "короче":
        messages[chat_id].append({"user": user, "text": text, "time": timestamp})
        print(f"Saved message from {user} in chat {chat_id}: {text}")

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize messages from the last 24 hours or since last request."""
    chat_id = update.effective_chat.id
    now = datetime.datetime.now()
    
    if chat_id not in messages or len(messages[chat_id]) == 0:
        await update.message.reply_text("короче некуда — новых сообщений нет.")
        return

    # Check if the command is for all-time summary
    command_text = update.message.text.lower()
    alltime_mode = "оллтайм" in command_text or "alltime" in command_text

    if alltime_mode:
        # Get all messages for all-time summary
        recent_msgs = messages[chat_id]
        summary_type = "всех сообщений"
    else:
        # Get last request time or default to 24 hours ago
        last_request = last_requests.get(chat_id, now - datetime.timedelta(days=1))
        recent_msgs = [m for m in messages[chat_id] if m["time"] > last_request]
        summary_type = "последних сообщений"

    if not recent_msgs:
        await update.message.reply_text("короче некуда — новых сообщений нет")
        return

    # Only update last request time for regular summaries, not all-time
    if not alltime_mode:
        last_requests[chat_id] = now

    # Prepare text for summarization
    text_to_summarize = "\n".join([f"{m['user']}: {m['text']}" for m in recent_msgs])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "используй lowercase. суммируй этот разговор максимально кратко и по пунктам, указывая автора по каждому пункту:"},
                {"role": "user", "content": text_to_summarize}
            ],
            max_tokens=3000
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        summary = "сори чет не получилось"

    await update.message.reply_text(f"🐳 саммари {summary_type}:\n{summary}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a start message."""
    await update.message.reply_text("привет, я бот для резюмирования чата. напиши 'короче' и я суммирую последние сообщения.")
    
def main() -> None:
    """Start the bot."""
    # Create the Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"(?i)короче"), save_message))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)короче"), summarize))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"(?i)короче(\s+оллтайм|\s+alltime)?"), save_message))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)короче(\s+оллтайм|\s+alltime)?"), summarize))

    # Start the Bot
    logger.info("бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
