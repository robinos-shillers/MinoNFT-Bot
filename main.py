
import logging
from bot import create_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    logging.info("Starting bot...")
    app = create_bot()
    logging.info("Bot created, starting polling...")
    app.run_polling()
    logging.info("Bot stopped")
