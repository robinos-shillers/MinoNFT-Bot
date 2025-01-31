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
    # Print columns for debugging
    print("Available columns:", df.columns.tolist())
    
    # Try to find the player column
    player_column = [col for col in df.columns if 'player' in col.lower()][0]
    player_data = df[df[player_column].str.lower() == player_name.lower()]

    if player_data.empty:
        return None

    info = player_data.iloc[0]
    return (f"🔹 *{info['Player']}* 🔹\n🎭 Rarity: {info['Rarity']}\n⚽ Position: {info['Position']}\n"
            f"🏟️ Club: {info['Club']}\n🌍 Country: {info['Country']}\n💰 Yearly Earnings: {info['Total Yearly Earnings']} sTLOS")