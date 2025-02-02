import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Spreadsheet
spreadsheet = client.open("Mino Football Earnings - 2024/25")
player_list_sheet = spreadsheet.worksheet("Player List")

def get_all_players():
    """Retrieve all player data."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    # Exclude retired players for active player lists
    active_players = df[df["Status"].str.lower() != "retired"]
    return active_players

def get_retired_players():
    """Retrieve retired players."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    retired_players = df[df["Status"].str.lower() == "retired"]
    return retired_players

def get_unique_values(field):
    """Retrieve unique values for Club, Rarity, or Country."""
    df = get_all_players()  # Only active players
    return sorted(df[field].dropna().unique())

def get_player_info(player_name):
    """Retrieve player details and NFT video link."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    player_data = df[df["Player"].str.lower() == player_name.lower()]

    if player_data.empty:
        return None

    info = player_data.iloc[0]
    info_text = (
        f"🔹 *{info['Player']}* 🔹\n"
        f"🎭 Rarity: {info['Rarity']}\n"
        f"⚽ Position: {info['Position']}\n"
        f"🏟️ Club: {info['Club']}\n"
        f"🌍 Country: {info['Country']}\n"
        f"💰 Total Earnings: {info['Total Earnings']}\n"
        f"💼 2024/25 Earnings: {info.get('2024/25 Earnings', 'N/A')}"
    )
    video_link = info.get("LINK", None)
    return info_text, video_link