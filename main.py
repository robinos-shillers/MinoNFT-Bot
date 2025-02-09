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

# Create and assign a persistent event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def initialize_bot():
    """Ensure the bot is properly initialized."""
    await telegram_app.initialize()

loop.run_until_complete(initialize_bot())  # Ensures bot starts with an event loop

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates asynchronously."""
    update_data = request.get_json()
    update = Update.de_json(update_data, telegram_app.bot)

    try:
        # ✅ Fix: Use create_task to prevent event loop conflicts
        asyncio.create_task(telegram_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
