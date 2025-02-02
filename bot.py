from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from google_sheets import get_player_info, get_all_players, get_unique_values, get_retired_players
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Enable Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Constants for pagination
ITEMS_PER_PAGE = 10

# 🎯 /players Command
async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user how they want to view the players."""
    keyboard = [
        [InlineKeyboardButton("🔤 Alphabetically", callback_data='sort_alpha')],
        [InlineKeyboardButton("🏟️ By Club", callback_data='filter_club')],
        [InlineKeyboardButton("⭐ By Rarity", callback_data='filter_rarity')],
        [InlineKeyboardButton("🌍 By Country", callback_data='filter_country')],
        [InlineKeyboardButton("👴 Retired Players", callback_data='filter_retired')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("How would you like to view the players?", reply_markup=reply_markup)


# Handle Sorting and Filtering
async def handle_sort_or_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        action = query.data

        if action == 'sort_alpha':
            df = get_all_players()
            players = df[df['Player'].notnull()]["Player"].sort_values().tolist()  # Ignore blanks
            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

        elif action == 'filter_retired':
            df = get_retired_players()
            players = df["Player"].dropna().tolist()
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

            keyboard = [[InlineKeyboardButton(option, callback_data=f'{action}_value_{option}')] for option in options]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Select a {field}:", reply_markup=reply_markup)

    except Exception as e:
        logging.error(f"Error in handle_sort_or_filter_selection: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")


# Handle Filter Value Selection
async def handle_filter_value_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_value_')
        filter_type, filter_value = data[0], data[1]

        field_map = {
            'filter_club': 'Club',
            'filter_rarity': 'Rarity',
            'filter_country': 'Country'
        }
        field = field_map[filter_type]

        df = get_all_players()
        players = df[df[field] == filter_value]["Player"].dropna().tolist()

        context.user_data['players_list'] = players
        context.user_data['current_page'] = 0

        await send_player_list(update, context, players, page=0)

    except Exception as e:
        logging.error(f"Error in handle_filter_value_selection: {e}")
        await query.edit_message_text("❌ An error occurred while filtering players.")


# Paginate Player List
async def send_player_list(update, context, players, page):
    """Display a paginated list of players."""
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_players = players[start:end]

    keyboard = [[InlineKeyboardButton(player, callback_data=f'player_{player}')] for player in current_players]

    # Pagination buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'prev_page_{page-1}'))
    if end < len(players):
        pagination_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f'next_page_{page+1}'))

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text="Select a player:", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("Select a player:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in send_player_list: {e}")
        await update.message.reply_text("❌ Failed to load players.")


# Handle Pagination
async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        players = context.user_data.get('players_list', [])
        page = int(query.data.split('_')[-1])
        context.user_data['current_page'] = page

        await send_player_list(update, context, players, page)

    except Exception as e:
        logging.error(f"Error in handle_pagination: {e}")
        await query.edit_message_text("❌ An error occurred while loading the page.")


# Handle Player Selection
async def handle_player_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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


# 🚀 Initialize the Bot
def create_bot():
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("players", players_command))

    # Callback Query Handlers
    application.add_handler(CallbackQueryHandler(handle_sort_or_filter_selection, pattern='^(sort_|filter_)'))
    application.add_handler(CallbackQueryHandler(handle_filter_value_selection, pattern='^(filter_.*_value_)'))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern='^(next_page_|prev_page_)'))
    application.add_handler(CallbackQueryHandler(handle_player_selection, pattern='^player_'))

    return application