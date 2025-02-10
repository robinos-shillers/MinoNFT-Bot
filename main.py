import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from bot import create_bot

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Create bot instance
telegram_app: Application = create_bot()

# ✅ Initialize bot asynchronously
async def initialize_bot():
    await telegram_app.initialize()
    await telegram_app.start()

# ✅ Start the event loop in a background thread
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(initialize_bot())

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    update_data = request.get_json()
    update = Update.de_json(update_data, telegram_app.bot)

    try:
        asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}")
        return "Internal Server Error", 500

# ✅ Set webhook manually (optional)
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Register the bot webhook with Telegram."""
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/{os.getenv('TELEGRAM_BOT_TOKEN')}"
    telegram_app.bot.setWebhook(webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
