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


# ✅ Data Cleaning (Internal Only)
def clean_data(df):
    """Trim whitespace and remove hidden characters without changing case."""
    for col in ['Player', 'Club', 'Country', 'Rarity']:
        df[col] = df[col].astype(str).str.strip().str.replace('\u200b', '')  # Remove hidden zero-width spaces
    return df


# ✅ Get Active Players
def get_all_players():
    """Get all active players from the spreadsheet."""
    try:
        data = player_list_sheet.get_all_records()
        df = pd.DataFrame(data)
        df = clean_data(df)
        logging.info(f"Retrieved {len(df)} players from spreadsheet")
        return df
    except Exception as e:
        logging.error(f"Error getting players: {e}")
        return pd.DataFrame()g Retired)
def get_all_players():
    """Retrieve all active players (excluding retired)."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    logging.info(f"Total players loaded: {len(df)}")

    df = clean_data(df)  # ✅ Clean data

    # Filter out retired players
    active_players = df[
        (~df['Club'].str.contains('Retired', case=False, na=False)) &
        (~df['Country'].str.contains('Retired', case=False, na=False)) &
        (df['Player'].notnull()) &
        (df['Player'].str.strip() != '')
    ]

    logging.info(f"Active players after filtering: {len(active_players)}")
    logging.info(f"Sample active players: {active_players['Player'].head().tolist()}")
    return active_players


# ✅ Get Players by Filter
def get_players_by_filter(field, value):
    """Retrieve players based on Club, Country, or Rarity filter."""
    logging.info(f"Executing get_players_by_filter for {field} = '{value}'")

    df = get_all_players()
    
    # Add more detailed logging
    logging.info(f"Total rows in dataframe: {len(df)}")
    logging.info(f"Sample of {field} values: {df[field].head().tolist()}")
    
    # Clean and normalize the data
    df[field] = df[field].astype(str).str.strip()
    value = str(value).strip()
    
    # Ensure data types and clean values
    df[field] = df[field].fillna('').astype(str).str.strip()
    value = str(value).strip()
    
    # Case-insensitive match
    mask = df[field].str.lower() == value.lower()
    filtered_df = df[mask]
    
    # Get players and log results
    players = filtered_df["Player"].dropna().tolist()
    logging.info(f"Found {len(players)} players for {field}={value}: {players}")
    
    return players


# ✅ Get Unique Filter Values
def get_unique_values(field):
    """Retrieve unique values for Club, Rarity, or Country, excluding 'Retired'."""
    df = get_all_players()

    if field in df.columns:
        unique_values = df[field].dropna().unique()

        # Remove 'Retired' and blank values
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
    df = clean_data(df)  # ✅ Clean data

    retired_players = df[
        (df['Club'].str.contains('Retired', case=False, na=False)) |
        (df['Country'].str.contains('Retired', case=False, na=False))
    ]
    logging.info(f"Retired players found: {len(retired_players)}")
    return retired_players


# ✅ Get Player Information
def get_player_info(player_name):
    """Retrieve player details and NFT video link."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    df = clean_data(df)  # ✅ Clean data

    player_data = df[df["Player"].str.strip().str.lower() == player_name.strip().lower()]

    if player_data.empty:
        logging.warning(f"No data found for player: {player_name}")
        return None

    info = player_data.iloc[0]

    # Detect 2024/25 Earnings Column
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

    video_link = info.get("LINK", None)
    logging.info(f"Player info retrieved for: {info['Player']}")
    return info_text, video_link