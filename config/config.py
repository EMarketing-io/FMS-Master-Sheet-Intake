import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

RUNNING_IN_STREAMLIT_CLOUD = False
try:
    import streamlit as st
    if os.getenv("STREAMLIT_RUNTIME", "") and "OPENAI_KEY" in st.secrets:
        RUNNING_IN_STREAMLIT_CLOUD = True
except ImportError:
    st = None

if RUNNING_IN_STREAMLIT_CLOUD:
    OPENAI_KEY = st.secrets["OPENAI_KEY"]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5-2025-08-07")
    WHISPER_MODEL = st.secrets.get("WHISPER_MODEL", "whisper-1")

    service_account_info = json.loads(st.secrets["GOOGLE_SA_JSON"])
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )

    GOOGLE_SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
    REGULAR_FOLDER_ID = st.secrets["REGULAR_FOLDER_ID"]
    KICKSTART_FOLDER_ID = st.secrets["KICKSTART_FOLDER_ID"]
    AUDIO_DRIVE_FOLDER_ID = st.secrets["AUDIO_DRIVE_FOLDER_ID"]
    WEBSITE_DRIVE_FOLDER_ID = st.secrets["WEBSITE_DRIVE_FOLDER_ID"]
    MOM_FOLDER_ID = st.secrets["MOM_FOLDER_ID"]
    ACTION_POINT_FOLDER_ID = st.secrets["ACTION_POINT_FOLDER_ID"]

else:
    from dotenv import load_dotenv
    load_dotenv()

    OPENAI_KEY = os.getenv("OPENAI_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-2025-08-07")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
    REGULAR_FOLDER_ID = os.getenv("REGULAR_FOLDER_ID", "")
    KICKSTART_FOLDER_ID = os.getenv("KICKSTART_FOLDER_ID", "")
    AUDIO_DRIVE_FOLDER_ID = os.getenv("AUDIO_DRIVE_FOLDER_ID", "")
    WEBSITE_DRIVE_FOLDER_ID = os.getenv("WEBSITE_DRIVE_FOLDER_ID", "")
    MOM_FOLDER_ID = os.getenv("MOM_FOLDER_ID", "")
    ACTION_POINT_FOLDER_ID = os.getenv("ACTION_POINT_FOLDER_ID", "")

    GOOGLE_SA_FILE = os.getenv("GOOGLE_SA_FILE", "config/google_service_account.json")
    if not os.path.exists(GOOGLE_SA_FILE):
        raise FileNotFoundError(
            f"Google Service Account file not found: {GOOGLE_SA_FILE}"
        )

    creds = Credentials.from_service_account_file(
        GOOGLE_SA_FILE,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )

if not GOOGLE_SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID is missing!")

client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Main")
dropdown_sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("Dropdown")
drive_service = build("drive", "v3", credentials=creds)

__all__ = [
    "OPENAI_KEY",
    "OPENAI_MODEL",
    "WHISPER_MODEL",
    "REGULAR_FOLDER_ID",
    "KICKSTART_FOLDER_ID",
    "AUDIO_DRIVE_FOLDER_ID",
    "WEBSITE_DRIVE_FOLDER_ID",
    "MOM_FOLDER_ID",
    "ACTION_POINT_FOLDER_ID",
    "creds",
    "client",
    "sheet",
    "dropdown_sheet",
    "drive_service",
]