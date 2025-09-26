import gspread
from google.oauth2.service_account import Credentials

READONLY_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
RW_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def make_gspread_client_from_file(sa_json_path: str, write: bool = False) -> gspread.Client:
    scopes = RW_SCOPES if write else READONLY_SCOPES
    creds = Credentials.from_service_account_file(sa_json_path, scopes=scopes)
    return gspread.authorize(creds)

def fetch_values(client: gspread.Client, spreadsheet_id: str, worksheet_name: str | None, rng: str):
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1
    return ws.get(rng) or []

def open_worksheet(clinet: gspread.client, spreadsheet_id: str, worksheet_name: str | None):
    sh= clinet.open_by_key(spreadsheet_id)
    return sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1