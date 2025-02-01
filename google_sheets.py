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

def get_player_info(player_name):
    """Retrieve player details and NFT video link."""
    df = pd.DataFrame(player_list_sheet.get_all_records())

    # Find player info
    player_data = df[df["Player Name"].str.lower() == player_name.lower()]

    if player_data.empty:
        return None

    info = player_data.iloc[0]

    # Prepare player details
    info_text = (
        f"🔹 *{info['Player Name']}* 🔹\n"
        f"🎭 Rarity: {info['Rarity']}\n"
        f"⚽ Position: {info['Position']}\n"
        f"🏟️ Club: {info['Club']}\n"
        f"🌍 Country: {info['Country']}\n"
        f"💰 Yearly Earnings: {info['Total Yearly Earnings']} sTLOS"
    )

    # Get the video link
    video_link = info.get("LINK", None)

    return info_text, video_link