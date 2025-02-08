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

# ✅ Get Telegram Bot Token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN is not set in environment variables.")

@app.route("/")
def home():
    """Basic route to check if the bot is running."""
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, telegram_app.bot)
        logging.info(f"📩 Received update: {update}")

        # Process update asynchronously
        asyncio.run(telegram_app.process_update(update))

        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Error in webhook processing: {e}")
        return "ERROR", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server for webhook handling...")

    # ✅ Get the port for Railway deployment (default to 8080)
    port = int(os.environ.get("PORT", 8080))

    # ✅ Start Flask server to handle webhooks
    app.run(host="0.0.0.0", port=port)
