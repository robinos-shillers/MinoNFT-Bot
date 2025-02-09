import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from bot import create_bot
from asgiref.sync import async_to_sync

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

asyncio.run(initialize_bot())  # Runs once at startup

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    try:
        update_data = request.get_json()
        logging.info(f"📩 Incoming update: {update_data}")  # Log full request

        update = Update.de_json(update_data, telegram_app.bot)

        # ✅ Ensure we execute async functions properly inside Flask
        async_to_sync(telegram_app.process_update)(update)

        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}", exc_info=True)
        return "Internal Server Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
