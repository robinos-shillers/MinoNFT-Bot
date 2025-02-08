import logging
import os
import asyncio
from flask import Flask, request
from bot import create_bot
from telegram import Update

# ✅ Logging Setup
logging.basicConfig(level=logging.INFO)

# ✅ Initialize Flask App
app = Flask(__name__)

# ✅ Initialize Telegram Bot
telegram_app = create_bot()

@app.route("/")
def home():
    return "MinoNFT Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
async def webhook():
    """Process Telegram webhook updates asynchronously."""
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        logging.info(f"📩 Received update: {update}")

        # Process update in background
        asyncio.create_task(telegram_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return "Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
