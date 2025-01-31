import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Spreadsheet
spreadsheet = client.open("Mino Football Earnings - 2024/25")

# Get sheet references dynamically
sheet_names = {sheet.title: sheet for sheet in spreadsheet.worksheets()}
player_list_sheet = sheet_names.get("Player List")

def get_player_info(player_name):
    """Retrieve player details from Player List."""
    df = pd.DataFrame(player_list_sheet.get_all_records())
    player_data = df[df["Player Name"].str.lower() == player_name.lower()]

    if player_data.empty:
        return None

    info = player_data.iloc[0]
    return (f"🔹 *{info['Player Name']}* 🔹\n🎭 Rarity: {info['Rarity']}\n⚽ Position: {info['Position']}\n"
            f"🏟️ Club: {info['Club']}\n🌍 Country: {info['Country']}\n💰 Yearly Earnings: {info['Total Yearly Earnings']} sTLOS")