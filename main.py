import logging
import os
from flask import Flask, request
from bot import create_bot
from telegram import Update
from telegram.ext import Application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize Flask app
app = Flask(__name__)

# Create bot instance
telegram_app: Application = create_bot()

@app.route("/")
def home():
    return "MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK", 200

if __name__ == "__main__":
    logging.info("Starting bot with Flask...")

    # Get the port for Railway (default to 5000)
    port = int(os.environ.get("PORT", 5000))

    # Start Flask server
    app.run(host="0.0.0.0", port=port)
