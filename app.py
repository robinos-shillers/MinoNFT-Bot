from flask import Flask, request
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application

# ✅ Logging
logging.basicConfig(level=logging.INFO)

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Get Bot Token from Environment Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)
app_telegram = Application.builder().token(TOKEN).build()

# ✅ Webhook Route (Telegram sends updates here)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Receive updates from Telegram and process them."""
    update = Update.de_json(request.get_json(), bot)
    app_telegram.process_update(update)
    return "OK", 200

# ✅ Set the Telegram Webhook
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Register the bot webhook with Telegram."""
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/{TOKEN}"
    bot.setWebhook(webhook_url)
    return f"Webhook set to {webhook_url}", 200

# ✅ Home Route
@app.route("/")
def home():
    return "MinoNFT Telegram Bot is running!", 200

# ✅ Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))