import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import logging

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)

# ✅ Load Google Sheets Credentials from Environment Variable
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not credentials_json:
    raise ValueError("❌ Google Cloud credentials not found in environment variables.")

# ✅ Parse the JSON string
credentials_dict = json.loads(credentials_json)

# ✅ Authorize with Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

# ✅ Open the Google Spreadsheet
spreadsheet = client.open("Mino Football Earnings - 2024/25")
player_list_sheet = spreadsheet.worksheet("Player List")

logging.info("✅ Successfully connected to Google Sheets.")

# ✅ Data Cleaning (Ensures No Hidden Characters)
def clean_data(df):
    """Trims whitespace, removes hidden characters, and ensures case consistency."""
    for col in ['Player', 'Club', 'Country', 'Rarity']:
        df[col] = df[col].astype(str).str.strip().str.replace('\u200b', '')  # Remove zero-width spaces
    return df

# ✅ Get Active Players (Excluding Retired)
def get_all_players():
    """Retrieve all active players, ensuring data is clean and sorted."""
    try:
        records = player_list_sheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty:
            logging.error("❌ Retrieved empty dataframe from sheets")
            return pd.DataFrame()

        df = clean_data(df)

        # Remove retired players
        active_players = df[
            (~df['Club'].str.contains('Retired', case=False, na=False)) &
            (~df['Country'].str.contains('Retired', case=False, na=False)) &
            (df['Player'].notnull()) &
            (df['Player'].str.strip() != '')
        ].copy()

        logging.info(f"✅ Total active players: {len(active_players)}")
        return active_players

    except Exception as e:
        logging.error(f"❌ Error getting players: {str(e)}")
        return pd.DataFrame()

# ✅ Get Players Alphabetically
def get_players_alphabetically():
    """Retrieve all active players in alphabetical order."""
    df = get_all_players()
    df = clean_data(df)  # Ensure data is clean

    if df.empty:
        logging.warning("⚠️ No active players found.")
        return []

    # Get all active players and sort them
    players = df["Player"].dropna().str.strip().unique().tolist()
    players = sorted(players, key=str.lower)  # Case-insensitive sorting

    logging.info(f"✅ Found {len(players)} players (Alphabetically)")
    return players

# ✅ Get Players by Filter
def get_players_by_filter(field, value):
    """Retrieve players based on Club, Country, or Rarity filter."""
    logging.info(f"🔍 Executing get_players_by_filter for {field} = '{value}'")

    df = get_all_players()
    if df.empty:
        logging.error("⚠️ No data available when filtering players.")
        return []

    # Normalize field for lookup
    df[field] = df[field].astype(str).str.strip()
    value = str(value).strip()

    # Case-insensitive matching
    mask = df[field].str.lower() == value.lower()
    filtered_df = df[mask]

    # Get list of players
    players = filtered_df["Player"].dropna().tolist()
    logging.info(f"✅ Found {len(players)} players for {field} = {value}")

    return players

# ✅ Get Unique Filter Values (Club, Country, Rarity)
def get_unique_values(field):
    """Retrieve unique values for Club, Rarity, or Country, excluding 'Retired'."""
    df = get_all_players()

    if df.empty:
        logging.error(f"No data found when retrieving unique values for {field}")
        return []

    if field in df.columns:
        unique_values = df[field].dropna().unique()

        # Remove "Retired" and blank values
        filtered_values = [
            value.strip() for value in unique_values
            if value.lower() != "retired" and value.strip() != ""
        ]

        logging.info(f"Unique values for {field}: {filtered_values}")
        return sorted(filtered_values)
    else:
        logging.warning(f"Field '{field}' not found in data.")
    return []

# ✅ Get Retired Players
def get_retired_players():
    """Retrieve retired players."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)

    retired_players = df[
        (df['Club'].str.contains('Retired', case=False, na=False)) |
        (df['Country'].str.contains('Retired', case=False, na=False))
    ]

    logging.info(f"Retired players found: {len(retired_players)}")
    return retired_players

# ✅ Get February 2025 Earnings
def get_february_earnings(page=0, items_per_page=10):
    """Retrieve top earners for February 2025 from the 'Earning Distribution' sheet, ignoring rows 155+."""
    try:
        earnings_sheet = spreadsheet.worksheet("Earning Distribution")
        df = pd.DataFrame(earnings_sheet.get_all_records())

        if "February" not in df.columns:
            logging.error("❌ 'February' column not found in the sheet.")
            return []

        # Get total payout from row 156
        total_payout = df.iloc[154]["February"] if len(df) > 154 else 0

        # Clean Player column
        df['Player'] = df['Player'].astype(str).str.strip().str.replace('\u200b', '', regex=False)

        # Convert February earnings to numeric
        df["February"] = pd.to_numeric(df["February"].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')

        # Exclude rows from index 154 onwards
        df = df.iloc[:153]

        # Sort by February earnings descending
        df = df.sort_values("February", ascending=False, na_position='last')

        # Pagination
        start = page * items_per_page
        end = start + items_per_page

        # Get records with pagination
        records = df.iloc[start:end][['Player', 'February']].to_dict('records')
        if records:
            records.append({'payout_note': f"The total amount paid out in February was {total_payout} sTLOS."})
        return records

    except Exception as e:
        logging.error(f"❌ Error retrieving February earnings: {str(e)}")
        return []

# Keep the January function for backward compatibility
def get_january_earnings(page=0, items_per_page=10):
    """Retrieve top earners for January 2025 from the 'Earning Distribution' sheet, ignoring rows 155+."""
    try:
        earnings_sheet = spreadsheet.worksheet("Earning Distribution")
        df = pd.DataFrame(earnings_sheet.get_all_records())

        if "January" not in df.columns:
            logging.error("❌ 'January' column not found in the sheet.")
            return []

        # Get total payout from row 156
        total_payout = df.iloc[154]["January"] if len(df) > 154 else 0

        # Clean Player column
        df['Player'] = df['Player'].astype(str).str.strip().str.replace('\u200b', '', regex=False)

        # Convert January earnings to numeric
        df["January"] = pd.to_numeric(df["January"].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')

        # Exclude rows from index 154 onwards
        df = df.iloc[:153]

        # Sort by January earnings descending
        df = df.sort_values("January", ascending=False, na_position='last')

        # Pagination
        start = page * items_per_page
        end = start + items_per_page

        # Get records with pagination
        records = df.iloc[start:end][['Player', 'January']].to_dict('records')
        if records:
            records.append({'payout_note': f"The total amount paid out in January was {total_payout} sTLOS."})
        return records

    except Exception as e:
        logging.error(f"❌ Error retrieving January earnings: {str(e)}")
        return []

# ✅ Get Player Information
def get_player_info(player_name):
    """Retrieve player details and NFT video link."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)

    # Case-insensitive search for player
    player_data = df[df["Player"].str.strip().str.lower() == player_name.strip().lower()]

    if player_data.empty:
        logging.warning(f"⚠️ No data found for player: {player_name}")
        return None

    info = player_data.iloc[0]

    # ✅ Handle 2024/25 Earnings Column
    earnings_2024_25_column = [col for col in df.columns if "2024/25" in col and "sTLOS" in col]
    earnings_2024_25 = info.get(earnings_2024_25_column[0], 'N/A') if earnings_2024_25_column else 'N/A'

    info_text = (
        f"🔹 *{info['Player']}* 🔹\n"
        f"🎭 Rarity: {info['Rarity']}\n"
        f"⚽ Position: {info['Position']}\n"
        f"🏟️ Club: {info['Club']}\n"
        f"🌍 Country: {info['Country']}\n"
        f"💰 Total Earnings: {info['Total Earnings']}\n"
        f"💼 2024/25 Earnings: {earnings_2024_25} sTLOS"
    )

    # ✅ Get NFT Video Link
    video_link = info.get("LINK", None)

    logging.info(f"✅ Player info retrieved for: {info['Player']}")
    return info_text, video_link

def get_player_earnings_chart(player_name):
    """Generate a line chart of player earnings over time."""
    earnings_sheet = client.open("Mino Football Earnings - 2024/25").worksheet("Earning Distribution")
    df = pd.DataFrame(earnings_sheet.get_all_records())

    # Get player's row
    player_data = df[df['Player'] == player_name]
    if player_data.empty:
        return None

    # Get weekly columns up to the blank column
    all_columns = df.columns.tolist()
    weekly_columns = []
    for col in all_columns:
        if col in ['Player', 'Total', 'Ballon d\'Or']:
            continue
        if pd.isna(col) or col.strip() == '':  # Stop at blank column
            break
        weekly_columns.append(col)

    # Convert values to numeric
    earnings = player_data[weekly_columns].iloc[0].apply(pd.to_numeric, errors='coerce')

    # Create chart
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(earnings)), earnings.values)
    plt.xticks(range(len(earnings)), earnings.index, rotation=45, ha='right')

    plt.title(f"{player_name}'s 2024/25 Season Earnings")
    plt.ylabel('sTLOS')
    plt.grid(False)  # Remove gridlines
    plt.tight_layout()

    # Save to bytes
    import io
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def get_top_earners(page=0, items_per_page=10):
    """Retrieve top earners of all time sorted by Total Earnings."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)

    # Convert Total Earnings to numeric, removing any currency symbols
    df['Total Earnings'] = pd.to_numeric(df['Total Earnings'].str.replace(r'[^\d.]', '', regex=True), errors='coerce')

    # Sort by Total Earnings descending
    df = df.sort_values('Total Earnings', ascending=False)

    # Format earnings with currency symbol
    df['Total Earnings'] = df['Total Earnings'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")

    # Calculate pagination
    start = page * items_per_page
    end = start + items_per_page

    return df.iloc[start:end][['Player', 'Total Earnings', 'Club', 'Country']].to_dict('records')

def get_current_season_earners(page=0, items_per_page=10):
    """Retrieve top earners for current season based on Total minus Ballon d'Or."""
    earnings_sheet = client.open("Mino Football Earnings - 2024/25").worksheet("Earning Distribution")
    df = pd.DataFrame(earnings_sheet.get_all_records())

    # Get the player with highest February earnings
    february_df = df.copy()
    february_df["February"] = pd.to_numeric(february_df["February"].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    february_df = february_df.iloc[:154]  # Exclude rows 155+
    top_february_player = february_df.nlargest(1, "February")["Player"].iloc[0] if not february_df.empty else None

    # Clean only Player column
    df['Player'] = df['Player'].astype(str).str.strip().str.replace('\u200b', '')

    # Convert current season earnings to numeric
    season_col = 'Total minus Ballon d\'Or'
    df[season_col] = df[season_col].astype(str)
    df[season_col] = pd.to_numeric(df[season_col].str.replace(r'[^\d.]', '', regex=True), errors='coerce')

    # Sort by current season earnings descending
    df = df.sort_values(season_col, ascending=False, na_position='last')

    # Calculate pagination
    start = page * items_per_page
    end = start + items_per_page

    # Mark the top February earner
    result_df = df.iloc[start:end][['Player', season_col]].copy()
    result_df['top_february'] = result_df['Player'] == top_february_player

    return result_df.to_dict('records')