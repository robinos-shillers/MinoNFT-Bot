import logging
import os
import asyncio
from flask import Flask, request, jsonify
from bot import create_bot
from telegram import Update

# ✅ Logging Configuration
logging.basicConfig(level=logging.INFO)

# ✅ Initialize Flask App
app = Flask(__name__)

# ✅ Initialize Telegram Bot
telegram_app = create_bot()

@app.route("/")
def home():
    return "✅ MinoNFT Telegram Bot is Running!"

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    """Process Telegram webhook updates."""
    try:
        update_data = request.get_json(force=True)
        logging.info(f"📩 Received update: {update_data}")

        update = Update.de_json(update_data, telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))  # Ensures async handling

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info("🚀 Starting Flask server...")
    port = int(os.getenv("PORT", 10000))  # Render defaults to 10000
    app.run(host="0.0.0.0", port=port)
