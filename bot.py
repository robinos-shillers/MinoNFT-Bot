from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from google_sheets import get_player_info  # Import functions from google_sheets.py

TOKEN = "7258778385:AAG9k6-RYAk7uH9tw0qGuXjkHSHcMeuf_4s"

def player_command(update: Update, context: CallbackContext):
    """Handle /player command."""
    if len(context.args) == 0:
        update.message.reply_text("Please provide a player name.")
        return

    player_name = " ".join(context.args)
    result = get_player_info(player_name)

    if result:
        update.message.reply_text(result, parse_mode="Markdown")
    else:
        update.message.reply_text(f"No data found for {player_name}.")

def create_bot():
    """Initialize the bot and add command handlers."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler("player", player_command))

    return updater