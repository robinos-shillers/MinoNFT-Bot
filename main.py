import logging
import os
import asyncio
from flask import Flask, request
from bot import create_bot
from telegram import Update

# ✅ Logging
logging.basicConfig(level=logging.INFO)

# ✅ Flask App
app = Flask(__name__)

# ✅ Telegram Bot
telegram_app = create_bot()

@app.route("/")
def home():
    return "MinoNFT Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
async def webhook():
    """Process Telegram updates."""
    try:
        logging.info("📩 Received Telegram update")
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.create_task(telegram_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return "Error", 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
