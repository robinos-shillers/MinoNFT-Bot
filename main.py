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

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates synchronously."""
    try:
        update_data = request.get_json()  # ✅ Remove `await`
        logging.info(f"📩 Incoming update: {update_data}")

        update = Update.de_json(update_data, telegram_app.bot)

        # Process update asynchronously
        asyncio.create_task(telegram_app.process_update(update))

        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {str(e)}", exc_info=True)
        return "Internal Server Error", 500

async def run_bot():
    """Run the bot and Flask app asynchronously."""
    await telegram_app.initialize()
    port = int(os.environ.get("PORT", 10000))
    logging.info("🚀 Starting Flask server...")
    await asyncio.to_thread(app.run, host="0.0.0.0", port=port)

if __name__ == "__main__":
    asyncio.run(run_bot())  # ✅ Run everything in a clean async loop
