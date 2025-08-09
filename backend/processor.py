import os
import tempfile
import requests
from config.config import (
    sheet,
    AUDIO_DRIVE_FOLDER_ID,
    WEBSITE_DRIVE_FOLDER_ID,
    MOM_FOLDER_ID,
    ACTION_POINT_FOLDER_ID,
    drive_service,
)
from backend.audio.transcription import transcribe_audio
from backend.audio.summarizer import generate_summary
from backend.audio.doc_generator import generate_docx

from backend.website.extract import extract_text_from_url
from backend.website.summarize import summarize_with_openai
from backend.website.document import generate_website_docx

from backend.drive_ops import upload_file_to_drive
from backend.sheet_ops import update_row_values


def download_file_from_drive(drive_url: str, output_path: str):
    file_id = drive_url.split("/d/")[1].split("/")[0]
    request = drive_service.files().get_media(fileId=file_id)
    with open(output_path, "wb") as f:
        resp = requests.get(f"https://drive.google.com/uc?export=download&id={file_id}")
        resp.raise_for_status()
        f.write(resp.content)


def _save_stream_to_path(stream, path: str):
    stream.seek(0)
    with open(path, "wb") as f:
        f.write(stream.read())


def _gs_hyperlink(url: str, text: str) -> str:
    """
    Return a Google Sheets HYPERLINK() formula:
    =HYPERLINK("url","text")
    Double quotes inside url/text must be doubled per Sheets escaping.
    """
    if not url:
        return text or ""
    safe_url = url.replace('"', '""')
    safe_text = (text or "").replace('"', '""')
    return f'=HYPERLINK("{safe_url}","{safe_text}")'


def process_row(row_idx: int, row_data: list):
    meeting_date = row_data[1]
    client_name = row_data[2]
    meeting_audio_link = row_data[6]
    website_link = row_data[7]

    # These are the exact column values we’ll write back:
    meeting_summary_cell = ""
    mom_summary_cell = ""
    action_points_cell = ""
    website_summary_cell = ""

    # ---------- AUDIO PIPELINE ----------
    if meeting_audio_link:
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp_audio:
            download_file_from_drive(meeting_audio_link, tmp_audio.name)
            transcript = transcribe_audio(tmp_audio.name)
            meeting_summary = generate_summary(transcript)

        # Full "Meeting Notes"
        meeting_notes_stream = generate_docx(
            meeting_summary, client_name, meeting_date, mode="full"
        )
        meeting_filename = f"{client_name}_{meeting_date}_Meeting Notes.docx"
        meeting_path = os.path.join(tempfile.gettempdir(), meeting_filename)
        _save_stream_to_path(meeting_notes_stream, meeting_path)
        meeting_url = upload_file_to_drive(meeting_path, AUDIO_DRIVE_FOLDER_ID)
        meeting_summary_cell = _gs_hyperlink(meeting_url, meeting_filename)

        # MoM Summary
        mom_stream = generate_docx(
            meeting_summary, client_name, meeting_date, mode="mom"
        )
        mom_filename = f"{client_name}_{meeting_date}_MoM Summary.docx"
        mom_path = os.path.join(tempfile.gettempdir(), mom_filename)
        _save_stream_to_path(mom_stream, mom_path)
        mom_url = upload_file_to_drive(mom_path, MOM_FOLDER_ID)
        mom_summary_cell = _gs_hyperlink(mom_url, mom_filename)

        # Action Points Summary
        action_stream = generate_docx(
            meeting_summary, client_name, meeting_date, mode="action"
        )
        action_filename = f"{client_name}_{meeting_date}_Action Points Summary.docx"
        action_path = os.path.join(tempfile.gettempdir(), action_filename)
        _save_stream_to_path(action_stream, action_path)
        action_url = upload_file_to_drive(action_path, ACTION_POINT_FOLDER_ID)
        action_points_cell = _gs_hyperlink(action_url, action_filename)

    # ---------- WEBSITE PIPELINE ----------
    if website_link and website_link.strip():
        page_text = extract_text_from_url(website_link.strip())
        website_summary = summarize_with_openai(page_text)
        website_stream = generate_website_docx(
            website_summary, client_name, meeting_date
        )
        website_filename = f"{client_name}_{meeting_date}_Website Summary.docx"
        website_path = os.path.join(tempfile.gettempdir(), website_filename)
        _save_stream_to_path(website_stream, website_path)
        website_url = upload_file_to_drive(website_path, WEBSITE_DRIVE_FOLDER_ID)
        website_summary_cell = _gs_hyperlink(website_url, website_filename)
    else:
        website_summary_cell = "NA"

    update_row_values(
        sheet,
        row_idx,
        {
            "Meeting Summary": meeting_summary_cell,
            "Website Summary": website_summary_cell,
            "MoM Summary": mom_summary_cell,
            "Action Points Summary": action_points_cell,
            "Status": "Done",
        },
    )
    print(f"✅ Row {row_idx} processed for client {client_name}")