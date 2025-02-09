import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from bot import create_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize Flask app
app = Flask(__name__)

# Create bot instance
telegram_app: Application = create_bot()

# Create a dedicated event loop for the bot
bot_loop = asyncio.new_event_loop()
asyncio.set_event_loop(bot_loop)

async def initialize_bot():
    """Ensure the bot is properly initialized."""
    await telegram_app.initialize()

# Start the bot's event loop
bot_loop.run_until_complete(initialize_bot())

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates asynchronously."""
    update_data = request.get_json()
    update = Update.de_json(update_data, telegram_app.bot)

    try:
        # ✅ FIX: Use run_coroutine_threadsafe to submit tasks to the running event loop
        asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), bot_loop)
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
