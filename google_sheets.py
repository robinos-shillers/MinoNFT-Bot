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


# ✅ Get Active Players (Excluding Retired)
def get_all_players():
    """Retrieve all active players (excluding retired)."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    logging.info(f"Total players loaded: {len(df)}")

    # Clean whitespace and standardize casing for filtering
    df['Player'] = df['Player'].astype(str).str.strip()
    df['Club'] = df['Club'].astype(str).str.strip()
    df['Country'] = df['Country'].astype(str).str.strip()
    df['Rarity'] = df['Rarity'].astype(str).str.strip()

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


# ✅ Get Players by Filter
def get_players_by_filter(field, value):
    """Retrieve players based on Club, Country, or Rarity filter."""
    df = get_all_players()

    # Standardize case and whitespace
    df[field] = df[field].astype(str).str.strip().str.lower()
    value = value.strip().lower()

    logging.info(f"Filtering players where {field} = '{value}'")
    logging.info(f"Available values for {field}: {df[field].unique()}")

    if field in df.columns:
        filtered_df = df[df[field] == value]
        players = filtered_df["Player"].dropna().tolist()

        logging.info(f"Players found for {value}: {players}")
        return players
    else:
        logging.warning(f"Field '{field}' not found in data.")
    return []


# ✅ Get Retired Players
def get_retired_players():
    """Retrieve retired players."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
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

    # Standardize player name
    df['Player'] = df['Player'].astype(str).str.strip().str.lower()
    player_name = player_name.strip().lower()

    player_data = df[df["Player"] == player_name]

    if player_data.empty:
        logging.warning(f"No data found for player: {player_name}")
        return None

    info = player_data.iloc[0]

    # Detect 2024/25 Earnings Column
    earnings_2024_25_column = [col for col in df.columns if "2024/25" in col and "sTLOS" in col]
    earnings_2024_25 = info.get(earnings_2024_25_column[0], 'N/A') if earnings_2024_25_column else 'N/A'

    info_text = (
        f"🔹 *{info['Player'].title()}* 🔹\n"
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