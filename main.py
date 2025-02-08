import logging
import os
import asyncio
from flask import Flask, request
from bot import create_bot
from telegram import Update
from telegram.ext import Application

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Create bot instance
telegram_app: Application = create_bot()

@app.route("/")
def home():
    return "MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates asynchronously."""
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.create_task(telegram_app.process_update(update))  # ✅ Run in background
        return "OK", 200
    except Exception as e:
        logging.error(f"Error handling webhook: {e}")
        return "Error", 500

if __name__ == "__main__":
    logging.info("Starting bot with Flask...")

    # ✅ Get the port for Railway (default to 8080 for Gunicorn)
    port = int(os.environ.get("PORT", 8080))

    # ✅ Run Flask with async support
    app.run(host="0.0.0.0", port=port)
