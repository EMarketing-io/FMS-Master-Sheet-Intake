# config.py
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

# OpenAI config
OPENAI_KEY = os.getenv("OPENAI_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-2025-08-07")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

# Google Service Account and scopes
GOOGLE_SA_FILE = os.getenv("GOOGLE_SA_FILE", "")
if not os.path.isabs(GOOGLE_SA_FILE):
    GOOGLE_SA_FILE = (
        os.path.join(os.path.dirname(__file__), os.pardir, GOOGLE_SA_FILE)
        if not os.path.exists(GOOGLE_SA_FILE)
        else GOOGLE_SA_FILE
    )
    GOOGLE_SA_FILE = os.path.abspath(GOOGLE_SA_FILE)
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Google Drive API scopes (Drive + Sheets)
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Drive folder IDs
REGULAR_FOLDER_ID = os.getenv("REGULAR_FOLDER_ID", "")
KICKSTART_FOLDER_ID = os.getenv("KICKSTART_FOLDER_ID", "")
AUDIO_DRIVE_FOLDER_ID = os.getenv("AUDIO_DRIVE_FOLDER_ID", "")
WEBSITE_DRIVE_FOLDER_ID = os.getenv("WEBSITE_DRIVE_FOLDER_ID", "")
MOM_FOLDER_ID = os.getenv("MOM_FOLDER_ID", "")
ACTION_POINT_FOLDER_ID = os.getenv("ACTION_POINT_FOLDER_ID", "")

# Initialize Google Credentials
if not GOOGLE_SA_FILE:
    raise ValueError("Missing GOOGLE_SA_FILE in .env")

creds = Credentials.from_service_account_file(GOOGLE_SA_FILE, scopes=SCOPES)

if not GOOGLE_SHEET_ID:
    raise ValueError("Missing GOOGLE_SHEET_ID in .env")

client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Main")
dropdown_sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Dropdown")
drive_service = build("drive", "v3", credentials=creds)

__all__ = [
    "OPENAI_KEY",
    "OPENAI_MODEL",
    "WHISPER_MODEL",
    "GOOGLE_SA_FILE",
    "GOOGLE_SHEET_ID",
    "REGULAR_FOLDER_ID",
    "KICKSTART_FOLDER_ID",
    "AUDIO_DRIVE_FOLDER_ID",
    "WEBSITE_DRIVE_FOLDER_ID",
    "MOM_FOLDER_ID",
    "ACTION_POINT_FOLDER_ID",
    "SCOPES",
    "creds",
    "client",
    "sheet",
    "dropdown_sheet",
    "drive_service",
]
