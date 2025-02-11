from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, Updater
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from google_sheets import (
    get_player_info,
    get_all_players,
    get_unique_values,
    get_players_by_filter,
    get_retired_players,
    get_players_alphabetically,
    get_top_earners,
    get_current_season_earners,
    get_player_earnings_chart
)
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
        [InlineKeyboardButton("📋 Show All", callback_data='filter_all')],
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
            players = get_players_alphabetically()

            if not players:
                await query.edit_message_text("❌ No players found.")
                return

            logging.info(f"✅ Found {len(players)} players (Alphabetically)")
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

            if not options:
                await query.edit_message_text(f"❌ No options found for {field}.")
                return

            logging.info(f"Available options for {field}: {options}")

            # Store options in context for pagination
            context.user_data['filter_options'] = options
            context.user_data['current_filter'] = action
            context.user_data['current_filter_page'] = 0
            await send_filter_options(update, context, options, 0, field)

        elif action == 'filter_retired':
            retired_df = get_retired_players()
            players = retired_df["Player"].dropna().tolist()
            logging.info(f"Retired players found: {players}")

            if not players:
                await query.edit_message_text("❌ No retired players found.")
                return

            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

        elif action == 'filter_all':
            df = get_all_players()
            players = df["Player"].dropna().tolist()
            logging.info(f"All players found: {len(players)}")

            if not players:
                await query.edit_message_text("❌ No players found.")
                return

            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

    except Exception as e:
        logging.error(f"❌ Error in handle_sort_or_filter_selection: {e}")
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
                await query.edit_message_text(f"❌ No players found for {filter_value}.")
                return

            logging.info(f"✅ Players found for {filter_value}: {players}")
            context.user_data['players_list'] = players
            context.user_data['current_page'] = 0
            await send_player_list(update, context, players, page=0)

    except Exception as e:
        logging.error(f"❌ Error in handle_filter_value_selection: {e}")
        await query.edit_message_text("❌ An error occurred while filtering players.")


async def send_filter_options(update, context, options, page, field):
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_options = options[start:end]

    if not current_options:
        await update.callback_query.edit_message_text("❌ No options found.")
        return

    action = context.user_data['current_filter']
    keyboard = [[InlineKeyboardButton(option, callback_data=f'{action}_value_{option}')] 
                for option in current_options]

    # Add pagination buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'filter_prev_{page-1}'))
    if end < len(options):
        pagination_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f'filter_next_{page+1}'))

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f"Select a {field}:", reply_markup=reply_markup)


# ✅ Send Player List (Pagination)
async def send_player_list(update, context, players, page):
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_players = players[start:end]

    if not current_players:
        await update.callback_query.edit_message_text("❌ No players found.")
        return

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
            keyboard = [[InlineKeyboardButton("📈 View Earnings Chart", callback_data=f'chart_{player_name}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if video_link:
                await query.message.reply_video(video=video_link, caption=info_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.message.reply_text(info_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await query.message.reply_text(f"❌ No data found for {player_name}.", parse_mode="Markdown")

    except Exception as e:
        logging.error(f"❌ Error in handle_player_selection: {e}")
        await query.edit_message_text("❌ An error occurred while loading player details.")


# ✅ Handle Player Command
async def player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_name = ' '.join(context.args)
    if not player_name:
        await update.message.reply_text("Please provide a player name. Example: /player Lionel Messi")
        return

    player_info = get_player_info(player_name)
    if player_info:
        info_text, video_link = player_info
        if video_link:
            await update.message.reply_video(video=video_link, caption=info_text, parse_mode="Markdown")
        else:
            await update.message.reply_text(info_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ No data found for {player_name}")

# ✅ Handle Pagination
async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    direction, page = query.data.split('_page_')
    page = int(page)

    if 'players_list' not in context.user_data:
        await query.edit_message_text("❌ No player list available.")
        return

    players = context.user_data['players_list']
    await send_player_list(update, context, players, page)

# ✅ Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 *Welcome to the Mino NFT Bot!*\n\n"
        "I help you explore Mino NFT players and their earnings.\n\n"
        "Get started with:\n"
        "🔍 */player <name>* - Look up a specific player\n"
        "📋 */players* - Browse all players\n"
        "💰 */earnings* - View top earners\n"
        "📈 */chart <name>* - View player's earnings chart\n"
        "❓ */help* - See detailed usage instructions\n\n"
        "Try */players* to start exploring!"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# ✅ Help Command
async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 All-Time Top Earners", callback_data='earnings_alltime_0')],
        [InlineKeyboardButton("📈 2024/25 Top Earners", callback_data='earnings_current_0')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("View top earners:", reply_markup=reply_markup)

async def handle_earnings_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, type_, page = query.data.split('_')
    page = int(page)

    if type_ == 'alltime':
        earners = get_top_earners(page)
        title = "💰 All-Time Top Earners"
        note = "_Earnings are the total $USD value taking in the current sTLOS price_"
        next_callback = f'earnings_alltime_{page+1}'
        prev_callback = f'earnings_alltime_{page-1}'
    else:
        earners = get_current_season_earners(page)
        title = "📈 2024/25 Season Top Earners"
        note = "_2024/25 season earnings are paid in sTLOS_"
        next_callback = f'earnings_current_{page+1}'
        prev_callback = f'earnings_current_{page-1}'

    if not earners:
        await query.edit_message_text("❌ No earnings data available.")
        return

    message = f"*{title}*\n{note}\n\n"
    for i, player in enumerate(earners, 1):
        earnings = player.get('Total Earnings' if type_ == 'alltime' else 'Total minus Ballon d\'Or', 0)
        message += f"{i}. *{player['Player']}* - {earnings}\n"

    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=prev_callback))
    if len(earners) == 10:  # If we have full page, assume there might be more
        keyboard.append(InlineKeyboardButton("➡️ Next", callback_data=next_callback))

    if keyboard:
        reply_markup = InlineKeyboardMarkup([keyboard])
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query.edit_message_text(message, parse_mode="Markdown")

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send earnings chart for a player."""
    if isinstance(update.callback_query, Update):
        player_name = ' '.join(context.args)
    else:
        player_name = update.callback_query.data.split('_')[1]
        update = update.callback_query
        await update.answer()

    if not player_name:
        await update.message.reply_text("Please provide a player name. Example: /chart Lionel Messi")
        return

    chart = get_player_earnings_chart(player_name)
    if chart:
        keyboard = [[InlineKeyboardButton(player_name, callback_data=f'player_{player_name}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=chart, caption=f"📈 Earnings chart for {player_name}", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"❌ No data found for {player_name}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "*📚 Mino NFT Bot Commands*\n\n"
        "*Basic Commands:*\n"
        "🔍 */player <name>* - Search for a specific player\n"
        "Example: /player Lionel Messi\n\n"
        "📋 */players* - Browse players with these filters:\n"
        "• Show all players\n"
        "• Filter by club\n"
        "• Filter by rarity\n"
        "• Filter by country\n"
        "• View retired players\n\n"
        "💰 */earnings* - View top earners (all-time and current season)\n"
        "📈 */chart <name>* - View player's earnings chart\n"
        "Example: /chart Lionel Messi\n\n"
        "*Tips:*\n"
        "• Use exact player names for best results\n"
        "• Navigate through lists using ⬅️ Next/Previous ➡️ buttons\n"
        "• Return to main menu using 🔙 Back button"
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")

# ✅ Initialize Bot
def create_bot():
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("players", players_command))
    application.add_handler(CommandHandler("player", player_command))
    application.add_handler(CommandHandler("earnings", earnings_command))
    application.add_handler(CommandHandler("chart", chart_command))

    # Callback Handlers
    application.add_handler(CallbackQueryHandler(handle_filter_value_selection, pattern='^filter_.*_value_.*$'))
    application.add_handler(CallbackQueryHandler(handle_sort_or_filter_selection, pattern='^(sort_|filter_(?!.*_value_).*)$'))
    application.add_handler(CallbackQueryHandler(handle_player_selection, pattern='^player_.*$'))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern='^(prev|next)_page_\d+$'))
    application.add_handler(CallbackQueryHandler(handle_filter_pagination, pattern='^filter_(prev|next)_\d+$'))
    application.add_handler(CallbackQueryHandler(handle_back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(handle_earnings_list, pattern='^earnings_.*$'))
    application.add_handler(CallbackQueryHandler(chart_command, pattern='^chart_.*$'))

    return application


async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📋 Show All", callback_data='filter_all')],
        [InlineKeyboardButton("🏟️ By Club", callback_data='filter_club')],
        [InlineKeyboardButton("⭐ By Rarity", callback_data='filter_rarity')],
        [InlineKeyboardButton("🌍 By Country", callback_data='filter_country')],
        [InlineKeyboardButton("👴 Retired Players", callback_data='filter_retired')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("How would you like to view the players?", reply_markup=reply_markup)


async def handle_filter_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    direction, page = query.data.split('_')[1:]
    page = int(page)

    if 'filter_options' not in context.user_data:
        await query.edit_message_text("❌ No filter options available.")
        return

    options = context.user_data['filter_options']
    field_map = {
        'filter_club': 'Club',
        'filter_rarity': 'Rarity',
        'filter_country': 'Country'
    }
    field = field_map[context.user_data['current_filter']]
    await send_filter_options(update, context, options, page, field)

async def handle_view_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        player_name = query.data.split('_')[2]
        await chart_command(update, context)
    except Exception as e:
        logging.error(f"Error handling view chart: {e}")
        await query.edit_message_text("An error occurred while loading the chart.")