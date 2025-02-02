import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

    # Filter out players where "Retired" appears in Club or Country
    active_players = df[
        (~df['Club'].str.contains('Retired', case=False, na=False)) &
        (~df['Country'].str.contains('Retired', case=False, na=False)) &
        (df['Player'].notnull()) &  # Exclude blank player names
        (df['Player'].str.strip() != '')  # Exclude players with empty spaces
    ]
    return active_players


# ✅ Get Retired Players
def get_retired_players():
    """Retrieve retired players."""
    df = pd.DataFrame(player_list_sheet.get_all_records())

    # Identify players with "Retired" in either Club or Country
    retired_players = df[
        (df['Club'].str.contains('Retired', case=False, na=False)) |
        (df['Country'].str.contains('Retired', case=False, na=False))
    ]
    return retired_players


# ✅ Get Unique Filter Values (Excluding "Retired")
def get_unique_values(field):
    """Retrieve unique values for Club, Rarity, or Country, excluding 'Retired'."""
    df = get_all_players()
    unique_values = df[field].dropna().unique()

    # Remove 'Retired' and blank values from the options
    filtered_values = [
        value for value in unique_values
        if value.lower() != "retired" and value.strip() != ""
    ]

    return sorted(filtered_values)


# ✅ Get Player Information
def get_player_info(player_name):
    """Retrieve player details and NFT video link."""
    df = pd.DataFrame(player_list_sheet.get_all_records())

    # Match player name case-insensitively
    player_data = df[df["Player"].str.lower() == player_name.lower()]

    if player_data.empty:
        return None

    info = player_data.iloc[0]

    # ✅ Player Details with Correct 2024/25 Earnings Column
    info_text = (
        f"🔹 *{info['Player']}* 🔹\n"
        f"🎭 Rarity: {info['Rarity']}\n"
        f"⚽ Position: {info['Position']}\n"
        f"🏟️ Club: {info['Club']}\n"
        f"🌍 Country: {info['Country']}\n"
        f"💰 Total Earnings: {info['Total Earnings']}\n"
        f"💼 2024/25 Earnings: {info.get('2024/25 sTLOS', 'N/A')}"
    )

    # ✅ Get NFT Video Link
    video_link = info.get("LINK", None)

    return info_text, video_link