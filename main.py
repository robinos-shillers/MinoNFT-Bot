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

# ✅ Ensure a running event loop
def get_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

loop = get_event_loop()

async def initialize_bot():
    """Ensure the bot is properly initialized and running."""
    await telegram_app.initialize()
    await telegram_app.start()
    logging.info("✅ Telegram bot started successfully!")

async def shutdown_bot():
    """Properly stop the bot on shutdown."""
    await telegram_app.stop()
    logging.info("🛑 Telegram bot stopped.")

# ✅ Initialize bot after Flask starts
@app.before_request
def start_bot():
    """Start the bot when Flask receives its first request."""
    if not hasattr(app, "bot_started"):
        loop.create_task(initialize_bot())
        app.bot_started = True  # Mark that bot has started

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates synchronously (fix TypeError)."""
    update_data = request.get_json()  # ❌ Removed 'await' (Flask is sync)
    update = Update.de_json(update_data, telegram_app.bot)

    try:
        loop.create_task(telegram_app.process_update(update))
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

    try:
        app.run(host="0.0.0.0", port=port)
    finally:
        logging.info("🛑 Shutting down bot...")
        loop.run_until_complete(shutdown_bot())
