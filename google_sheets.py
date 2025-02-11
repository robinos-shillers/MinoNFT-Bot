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


# ✅ Get January 2025 Earnings
def get_january_earnings(page=0, items_per_page=10):
    """Retrieve top earners for January 2025 from the 'Earning Distribution' sheet."""
    try:
        earnings_sheet = spreadsheet.worksheet("Earning Distribution")
        df = pd.DataFrame(earnings_sheet.get_all_records())

        if "January" not in df.columns:
            logging.error("❌ 'January' column not found in the sheet.")
            return []

        # Clean Player column
        df['Player'] = df['Player'].astype(str).str.strip().str.replace('\u200b', '', regex=False)

        # Convert January earnings to numeric
        df["January"] = pd.to_numeric(df["January"].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')

        # Sort by January earnings descending
        df = df.sort_values("January", ascending=False, na_position='last')

        # Pagination
        start = page * items_per_page
        end = start + items_per_page

        return df.iloc[start:end][['Player', 'January']].to_dict('records')

    except Exception as e:
        logging.error(f"❌ Error retrieving January earnings: {str(e)}")
        return []
