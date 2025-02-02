from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from google_sheets import get_player_info, get_all_players, get_unique_values, get_players_by_filter, get_retired_players
import os

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)

# ✅ Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Constants
ITEMS_PER_PAGE = 10


# ✅ /players Command
async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔤 Alphabetically", callback_data='sort_alpha')],
        [InlineKeyboardButton("🏟️ By Club", callback_data='filter_club')],
        [InlineKeyboardButton("⭐ By Rarity", callback_data='filter_rarity')],
        [InlineKeyboardButton("🌍 By Country", callback_data='filter_country')],
        [InlineKeyboardButton("👴 Retired Players", callback_data='filter_retired')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("How would you like to view the players?", reply_markup=reply_markup)


# ✅ Handle Sorting & Filter Selection
async def handle_sort_or_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    logging.info(f"Received action: {action}")  # Log the callback data

    try:
        if action == 'sort_alpha':
            df = get_all_players()
            players = df[df['Player'].notnull()]["Player"].sort_values().tolist()
            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

        elif action in ['filter_club', 'filter_rarity', 'filter_country']:
            field_map = {
                'filter_club': 'Club',
                'filter_rarity': 'Rarity',
                'filter_country': 'Country'
            }
            field = field_map[action]
            options = get_unique_values(field)

            logging.info(f"Available options for {field}: {options}")

            keyboard = [[InlineKeyboardButton(option, callback_data=f'{action}_value_{option}')] for option in options]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Select a {field}:", reply_markup=reply_markup)

        elif action == 'filter_retired':
            retired_df = get_retired_players()
            players = retired_df["Player"].dropna().tolist()
            logging.info(f"Retired players found: {players}")

            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

    except Exception as e:
        logging.error(f"Error in handle_sort_or_filter_selection: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")


# ✅ Handle Filter Value Selection
async def handle_filter_value_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logging.info(f"Received filter selection callback data: {query.data}")  # Log the callback data

    try:
        action = query.data
        if '_value_' in action:
            filter_type, filter_value = action.split('_value_')
            
            field_map = {
                'filter_club': 'Club',
                'filter_rarity': 'Rarity',
                'filter_country': 'Country'
            }
            field = field_map.get(filter_type)
            
            logging.info(f"Filtering by {field}: {filter_value}")
            
            players = get_players_by_filter(field, filter_value)
            
            if not players:
                await query.edit_message_text(f"No players found for {filter_value}")
                return
                
            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

        logging.info(f"Players found for {filter_value}: {players}")

        if not players:
            await query.edit_message_text(f"❌ No players found for {filter_value}.")
            return

        context.user_data['players_list'] = players
        context.user_data['current_page'] = 0

        await send_player_list(update, context, players, page=0)

    except Exception as e:
        logging.error(f"Error in handle_filter_value_selection: {e}")
        await query.edit_message_text("❌ An error occurred while filtering players.")


# ✅ Send Player List (Pagination)
async def send_player_list(update, context, players, page):
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_players = players[start:end]

    keyboard = [[InlineKeyboardButton(player, callback_data=f'player_{player}')] for player in current_players]

    # Pagination Buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'prev_page_{page-1}'))
    if end < len(players):
        pagination_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f'next_page_{page+1}'))

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text="Select a player:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Select a player:", reply_markup=reply_markup)


# ✅ Handle Player Selection
async def handle_player_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logging.info(f"Player selection callback data: {query.data}")  # Log player selection

    try:
        player_name = query.data.split('_', 1)[1]
        player_info = get_player_info(player_name)

        if player_info:
            info_text, video_link = player_info
            if video_link:
                await query.message.reply_video(video=video_link, caption=info_text, parse_mode="Markdown")
            else:
                await query.message.reply_text(info_text, parse_mode="Markdown")
        else:
            await query.message.reply_text(f"❌ No data found for `{player_name}`.", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error in handle_player_selection: {e}")
        await query.edit_message_text("❌ An error occurred while loading player details.")


# ✅ Initialize Bot
def create_bot():
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("players", players_command))

    # Callback Handlers
    application.add_handler(CallbackQueryHandler(handle_filter_value_selection, pattern='^filter_.*_value_.*$'))
    application.add_handler(CallbackQueryHandler(handle_sort_or_filter_selection, pattern='^(sort_|filter_(?!.*_value_).*)$'))
    application.add_handler(CallbackQueryHandler(handle_player_selection, pattern='^player_.*$'))

    return application