import logging
import os
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
async def home():
    return "✅ MinoNFT Telegram Bot is Running!"


@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
async def webhook():
    """Handle incoming Telegram updates."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, telegram_app.bot)

        logging.info(f"📩 Received update: {update_data}")

        # ✅ Process the update asynchronously
        await telegram_app.process_update(update)
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Webhook processing error: {e}")
        return "ERROR", 500


if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")

    # ✅ Get the port for Render deployment (default to 10000)
    port = int(os.environ.get("PORT", 10000))

    # ✅ Start Flask server in async mode
    app.run(host="0.0.0.0", port=port)
