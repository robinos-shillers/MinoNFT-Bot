from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
import os
from google_sheets import get_top_earners, get_current_season_earners, get_january_earnings

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)

# ✅ Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ✅ /earnings Command
async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /earnings command."""
    keyboard = [
        [InlineKeyboardButton("💰 All-Time Top Earners", callback_data="earnings_all_time")],
        [InlineKeyboardButton("📈 2024/25 Season Earnings", callback_data="earnings_current_season")],
        [InlineKeyboardButton("📊 January 2025 Earnings", callback_data="earnings_january")],  # ✅ New option
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an earnings category:", reply_markup=reply_markup)


# ✅ Handle Earnings Selection
async def handle_earnings_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the selection of earnings categories."""

    query = update.callback_query
    await query.answer()

    action = query.data
    earnings = []
    title = ""

    if action == "earnings_all_time":
        earnings = get_top_earners()
        title = "🏆 All-Time Top Earners"
    elif action == "earnings_current_season":
        earnings = get_current_season_earners()
        title = "📅 2024/25 Season Earnings"
    elif action == "earnings_january":  # ✅ New case for January earnings
        earnings = get_january_earnings()
        title = "📊 January 2025 Earnings"
    else:
        return

    if not earnings:
        await query.edit_message_text("⚠️ No earnings data available.")
        return

    message = f"{title}:\n\n"
    for idx, record in enumerate(earnings, start=1):
        earnings_value = record.get('January', record.get('Total Earnings', 0))
        message += f"{idx}. {record['Player']} - {earnings_value} sTLOS\n"

    await query.edit_message_text(message)


# ✅ Initialize Bot
def create_bot():
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("earnings", earnings_command))

    # Callback Handlers
    application.add_handler(CallbackQueryHandler(handle_earnings_selection, pattern='^earnings_.*$'))

    return application
