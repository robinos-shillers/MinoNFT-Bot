import logging
import os
from flask import Flask, request
from bot import create_bot
from telegram import Update
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize Flask app
app = Flask(__name__)

# Create bot instance
telegram_app = create_bot()

@app.route("/")
def home():
    return "MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
async def webhook():
    """Handle incoming Telegram updates."""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    # Ensure async processing
    asyncio.create_task(telegram_app.process_update(update))

    return "OK", 200

if __name__ == "__main__":
    logging.info("Starting bot with Flask...")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
