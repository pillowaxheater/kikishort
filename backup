import logging
import os
import datetime
from telethon import TelegramClient, events
import asyncio
import openai  # Use old-style import
import re  # Added for regex pattern matching

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

# OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_key")
openai.api_key = OPENAI_API_KEY  # Set key in old-style way

# Track last request time per chat
last_requests = {}

# Initialize the Telegram client (without starting it yet)
bot = TelegramClient('bot_session', API_ID, API_HASH)

async def get_chat_history(chat_id, limit=100, since_hours=240):
    """Get chat history from Telegram"""
    messages = []
    last_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=since_hours)
    
    async for message in bot.iter_messages(chat_id, limit=limit):
        if message.text and not message.text.lower().startswith("короче") and message.date > last_date:
            if message.sender:
                sender = await message.get_sender()
                sender_name = sender.first_name if hasattr(sender, 'first_name') else "Unknown"
            else:
                sender_name = "Unknown"
                
            messages.append({
                "user": sender_name,
                "text": message.text,
                "time": message.date
            })
    
    return messages

@bot.on(events.NewMessage(pattern=r"(?i)короче(\s+оллтайм|\s+alltime)?"))
async def handle_summary_command(event):
    """Handle the 'короче' command"""
    chat_id = event.chat_id
    now = datetime.datetime.now(datetime.timezone.utc)
    summary_type = "сообщений"  # Default value to prevent UnboundLocalError
    
    # Check if the command is for all-time summary
    command_text = event.text.lower()
    alltime_mode = "оллтайм" in command_text or "alltime" in command_text
    
    try:
        if alltime_mode:
            # Get all accessible history for all-time mode (limited to 100 messages)
            messages = await get_chat_history(chat_id, limit=100, since_hours=24*30)
            summary_type = "всех сообщений"
        else:
            # Get messages since last request or last 24 hours
            last_request = last_requests.get(chat_id, now - datetime.timedelta(hours=24))
            hours_since = (now - last_request).total_seconds() / 3600
            messages = await get_chat_history(chat_id, limit=100, since_hours=hours_since)
            last_requests[chat_id] = now
            summary_type = "последних сообщений"
        
        if not messages:
            await event.respond("короче некуда — новых сообщений нет")
            return
            
        # Prepare text for summarization
        text_to_summarize = "\n".join([f"{m['user']}: {m['text']}" for m in messages])
        
        # Generate summary with OpenAI (old-style API)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "используй lowercase. суммируй этот разговор максимально кратко и по пунктам, указывая автора по каждому пункту:"},
                {"role": "user", "content": text_to_summarize}
            ],
            max_tokens=5000
        )
        summary = response["choices"][0]["message"]["content"].strip()
        
    except Exception as e:
    logger.error(f"Error detail: {str(e)}")
    summary = "сори чет не получилось"
    
    await event.respond(f"📌 короче ({summary_type}):\n{summary}")

@bot.on(events.NewMessage(pattern=r"/start"))
async def start_command(event):
    """Handle the /start command"""
    await event.respond("привет, я бот для резюмирования чата. напиши 'короче' и я суммирую последние сообщения.")

async def main():
    """Start the bot and run it until disconnected"""
    # Start the bot here instead of at module level
    await bot.start(bot_token=BOT_TOKEN)
    print("Bot started successfully!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
