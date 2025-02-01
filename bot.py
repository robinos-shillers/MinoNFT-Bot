from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
from google_sheets import get_player_info  # Ensure this returns the link too

import os
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Enable Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /player command to fetch player info and send video."""
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide a player name.\nExample: `/player Lionel Messi`", parse_mode="Markdown")
        return

    player_name = " ".join(context.args)
    logging.info(f"User requested info for: {player_name}")

    # ⬇️ This should now return both info_text and link
    player_info = get_player_info(player_name)

    if player_info:
        info_text, video_link = player_info

        # Send player info first
        await update.message.reply_text(info_text, parse_mode="Markdown")

        # Send the video (if available)
        if video_link:
            try:
                await update.message.reply_video(video=video_link)
            except Exception as e:
                logging.error(f"Error sending video: {e}")
                await update.message.reply_text("⚠️ Unable to load the video for this player.")
    else:
        await update.message.reply_text(f"❌ No data found for `{player_name}`.", parse_mode="Markdown")

def create_bot():
    """Initializes the bot and registers command handlers."""
    application = Application.builder().token(TOKEN).build()

    # ✅ Add handlers
    application.add_handler(CommandHandler("player", player_command))

    return application