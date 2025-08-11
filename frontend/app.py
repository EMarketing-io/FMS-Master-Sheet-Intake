# app.py
import sys, os, io, ssl, time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime as dt
import streamlit as st
from pytz import timezone
from ssl import SSLEOFError
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from config.config import (
    sheet,
    dropdown_sheet,
    REGULAR_FOLDER_ID,
    KICKSTART_FOLDER_ID,
    drive_service,
)
from utils.sheet_client import (
    get_client_list,
    get_employee_email_map,
    append_main_row_in_order,
)
from utils.validators import is_valid_url

st.set_page_config(
    page_title="FMS Master Sheet - Intake", page_icon="📝", layout="wide"
)
st.markdown(
    """
<style>
.block-container {max-width: 1100px; padding-top: 1.5rem; padding-bottom: 3rem;}
.fms-header {text-align: center; padding: 1rem 0 1.5rem 0;}
.fms-header h1 {
    font-weight: 800; font-size: 2.2rem; margin-bottom: .3rem;
    background: -webkit-linear-gradient(45deg, #ff4b1f, #1fddff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.fms-subtitle {font-size: 1.05rem; color: var(--text-color-muted, rgba(140,140,160,.85));}
div[data-testid="stForm"] {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(8px);
    border-radius: 16px;
    border: 1px solid rgba(120,120,120,0.15);
    padding: 26px 30px 18px 30px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
@media (prefers-color-scheme: dark) {div[data-testid="stForm"] { background: rgba(40,40,40,0.65);}}
label {font-weight: 700 !important; margin-bottom: .2rem !important;}
/* File uploader custom style */
.stFileUploader > section {
    border: 2px dashed rgba(120,120,120,0.4) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    background: rgba(255,255,255,0.04);
    text-align: center;
}
.stFileUploader > section:hover {
    border-color: #1fddff !important;
    background: rgba(31,221,255,0.05);
}
/* Full-width submit button */
div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.02em;
    border: none;
    background: linear-gradient(45deg, #ff4b1f, #ff9068);
    color: white;
    transition: all 0.2s ease-in-out;
}
div[data-testid="stFormSubmitButton"] button:hover {
    filter: brightness(1.05);
    transform: translateY(-1px);
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="fms-header">
  <h1>🗂️ FMS Master Sheet — Intake</h1>
  <div class="fms-subtitle">Submit website/audio & metadata — we’ll handle the rest 🚀</div>
</div>
""",
    unsafe_allow_html=True,
)

try:
    clients = get_client_list(dropdown_sheet)
    employee_email = get_employee_email_map(dropdown_sheet)

except Exception as e:
    st.error(f"Failed to load dropdowns from Google Sheet: {e}")
    st.stop()


def _on_change_submitted_by():
    name = st.session_state.get("submitted_by", "")
    st.session_state["email_id"] = employee_email.get(name, "")


if "submitted_by" not in st.session_state:
    st.session_state["submitted_by"] = (
        list(employee_email.keys())[0] if employee_email else ""
    )
if "email_id" not in st.session_state:
    st.session_state["email_id"] = employee_email.get(
        st.session_state["submitted_by"], ""
    )

st.selectbox(
    "👤 Submitted By",
    options=list(employee_email.keys()) or ["—"],
    key="submitted_by",
    on_change=_on_change_submitted_by,
)
st.text_input("✉️ Email ID", key="email_id", disabled=True)


def robust_upload_to_drive_with_progress(
    data: bytes, filename: str, parent_folder_id: str
) -> str:
    stream = io.BytesIO(data)
    stream.seek(0)
    file_metadata = {"name": filename, "parents": [parent_folder_id]}

    media = MediaIoBaseUpload(
        stream,
        mimetype="application/octet-stream",
        resumable=True,
        chunksize=5 * 1024 * 1024,
    )

    progress = st.progress(0, text=f"Starting upload for {filename}...")
    retries = 5

    for attempt in range(1, retries + 1):
        try:
            request = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    progress.progress(
                        percent, text=f"Uploading {filename}... {percent}%"
                    )
            progress.progress(100, text=f"Upload complete ✅ ({filename})")
            return response["id"]

        except (HttpError, SSLEOFError, ssl.SSLError, ConnectionError) as e:
            if attempt < retries:
                wait = 2**attempt
                progress.progress(0, text=f"Retrying in {wait}s due to error: {e}")
                time.sleep(wait)
                stream.seek(0)
                continue
            raise RuntimeError(f"❌ Upload failed after {retries} attempts: {e}")


with st.form("intake_form"):
    col1, col2 = st.columns([1, 1])

    with col1:
        ist_today = dt.datetime.now(timezone("Asia/Kolkata")).date()
        meeting_date = st.date_input("🗓️ Meeting Date", max_value=ist_today)
        client_name = st.selectbox(
            "🏷️ Client Name", options=clients or ["—"], index=0 if clients else 0
        )
        meeting_type = st.selectbox("📌 Meeting Type", options=["Regular", "Kickstart"])

    with col2:
        website_link = st.text_input(
            "🌐 Website Link", placeholder="https://example.com"
        )
        audio_files = st.file_uploader(
            "🎙️ Meeting Audio Files (1–4 · .m4a/.mp3/.wav)",
            type=["m4a", "mp3", "wav"],
            accept_multiple_files=True,
        )

    submitted = st.form_submit_button("🚀 Submit", use_container_width=True)

if submitted:
    if not audio_files or len(audio_files) == 0:
        st.error("🎧 Please upload at least one meeting audio file before submitting.")
        st.stop()

    # Soft limit to avoid accidental huge batches; tweak as needed
    if len(audio_files) > 4:
        st.error("You can upload a maximum of 4 audio files at once.")
        st.stop()

    if website_link and not is_valid_url(website_link):
        st.error("Please enter a valid Website Link.")
        st.stop()

    ist = timezone("Asia/Kolkata")
    timestamp = dt.datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    meeting_date_str = meeting_date.strftime("%d-%m-%Y")

    try:
        parent_folder = (
            REGULAR_FOLDER_ID
            if meeting_type.lower() == "regular"
            else KICKSTART_FOLDER_ID
        )

        uploaded_links = []
        for idx, f in enumerate(audio_files, start=1):
            file_bytes = f.read()
            # derive extension from each uploaded file
            ext = f.name.split(".")[-1]
            safe_client_name = client_name.replace("/", "-").replace("\\", "-").strip()
            # Disambiguate filenames when multiple files are uploaded
            suffix = f"_{idx}" if len(audio_files) > 1 else ""
            filename = f"{safe_client_name}_{meeting_date_str}{suffix}.{ext}"

            file_id = robust_upload_to_drive_with_progress(
                file_bytes, filename, parent_folder
            )
            uploaded_links.append(f"https://drive.google.com/file/d/{file_id}/view")

        # Build the comma-separated string wrapped in parentheses: (link, link)
        meeting_audio_links_cell = f"({', '.join(uploaded_links)})"

        row = [
            timestamp,
            meeting_date_str,
            client_name,
            meeting_type,
            st.session_state["submitted_by"],
            st.session_state["email_id"],
            meeting_audio_links_cell,  # <-- multiple links in parentheses
            website_link,
            "",
            "",
            "",
            "",
            "Processing",
        ]
        append_main_row_in_order(sheet, row)

        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #28a745, #20c997);
            padding: 14px 18px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 1rem;
        ">
            ✅ Submitted! Your entry has been recorded
        </div>
        """,
            unsafe_allow_html=True,
        )

        # List out all uploaded audio links
        st.markdown(
            "<div style='margin-top: 1.2rem;'>"
            "<span style='font-size: 0.95rem; font-weight: 600;'>🎧 Audio uploaded:</span>",
            unsafe_allow_html=True,
        )
        for link in uploaded_links:
            st.markdown(
                f"""<div style="
                        margin-top: 0.5rem;
                        padding: 12px 16px;
                        border-radius: 10px;
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                    ">
                        <a href="{link}" target="_blank" style="color: #1fddff; text-decoration: none;">
                            {link}
                        </a>
                    </div>""",
                unsafe_allow_html=True,
            )

        if website_link:
            st.markdown(
                f"""
            <div style="
                margin-top: 0.8rem;
                padding: 12px 16px;
                border-radius: 10px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <span style="font-size: 0.95rem; font-weight: 600;">🔗 Website link:</span><br>
                <a href="{website_link}" target="_blank" style="color: #1fddff; text-decoration: none;">
                    {website_link}
                </a>
            </div>
            """,
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.error(f"Failed: {e}")