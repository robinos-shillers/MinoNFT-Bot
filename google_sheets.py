import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import logging

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)

# ✅ Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ✅ Open the Google Spreadsheet
spreadsheet = client.open("Mino Football Earnings - 2024/25")
player_list_sheet = spreadsheet.worksheet("Player List")


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
    logging.info(f"🔎 First 5 Players: {players[:5]}")

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


# ✅ Get Player Information
def get_top_earners(page=0, items_per_page=10):
    """Retrieve top earners of all time sorted by Total Earnings."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)
    
    # Convert Total Earnings to numeric, removing any currency symbols
    df['Total Earnings'] = pd.to_numeric(df['Total Earnings'].str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    
    # Sort by Total Earnings descending
    df = df.sort_values('Total Earnings', ascending=False)
    
    # Calculate pagination
    start = page * items_per_page
    end = start + items_per_page
    
    return df.iloc[start:end][['Player', 'Total Earnings', 'Club', 'Country']].to_dict('records')

def get_current_season_earners(page=0, items_per_page=10):
    """Retrieve top earners for current season (2024/25)."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)
    
    # Convert current season earnings to numeric
    season_col = '2024/25\nsTLOS'  # Updated column name to match spreadsheet
    df[season_col] = df[season_col].astype(str)  # Convert to string first
    df[season_col] = pd.to_numeric(df[season_col].str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    
    # Sort by current season earnings descending
    df = df.sort_values(season_col, ascending=False, na_position='last')
    
    # Calculate pagination
    start = page * items_per_page
    end = start + items_per_page
    
    return df.iloc[start:end][['Player', season_col, 'Club', 'Country']].to_dict('records')

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
        f"💰 Total Earnings: {info['Total Earnings']} sTLOS\n"
        f"💼 2024/25 Earnings: {earnings_2024_25} sTLOS"
    )

    # ✅ Get NFT Video Link
    video_link = info.get("LINK", None)

    logging.info(f"✅ Player info retrieved for: {info['Player']}")
    return info_text, video_link