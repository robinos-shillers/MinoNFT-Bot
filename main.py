import logging
import time
from bot import create_bot
from telegram.error import NetworkError, TelegramError

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_bot():
    """Runs the bot with polling and automatic restarts on failure."""
    app = create_bot()
    logging.info("🤖 Bot created, starting polling...")

    while True:
        try:
            app.run_polling()
        except NetworkError as e:
            logging.warning(f"🌐 NetworkError: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait before retrying
        except TelegramError as e:
            logging.error(f"❌ TelegramError: {e}. Retrying in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logging.critical(f"🚨 Unexpected error: {e}. Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    logging.info("🚀 Starting bot...")
    run_bot()
    logging.info("🛑 Bot stopped")
