
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
from google_sheets import get_player_info

TOKEN = "7258778385:AAG9k6-RYAk7uH9tw0qGuXjkHSHcMeuf_4s"

async def player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /player command."""
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a player name.")
        return

    player_name = " ".join(context.args)
    result = get_player_info(player_name)

    if result:
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"No data found for {player_name}.")

def create_bot():
    """Initialize the bot and add command handlers."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("player", player_command))
    return application
