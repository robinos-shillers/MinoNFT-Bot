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

# Ensure bot initialization
async def initialize_bot():
    """Ensure the bot is properly initialized."""
    await telegram_app.initialize()

# Create a persistent event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(initialize_bot())  # Run bot initialization once

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    try:
        update_data = request.get_json()
        logging.info(f"📩 Incoming update: {update_data}")

        update = Update.de_json(update_data, telegram_app.bot)

        # ✅ Ensure async updates are handled in a persistent event loop
        future = asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
        future.result()  # Wait for execution

        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}", exc_info=True)
        return "Internal Server Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
