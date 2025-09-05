# backend/processor.py
import os
import tempfile
import re
from typing import List

from config.config import (
    sheet,
    AUDIO_DRIVE_FOLDER_ID,
    WEBSITE_DRIVE_FOLDER_ID,
    MOM_FOLDER_ID,
    ACTION_POINT_FOLDER_ID,
    output_sheet,      # Output sheet handle (can be None if not configured)
    OUTPUT_SHEET_ID,   # For logging
    OUTPUT_SHEET_TAB,  # For logging
)
from backend.audio.transcription import transcribe_audio
from backend.audio.summarizer import generate_summary
from backend.audio.doc_generator import generate_docx

from backend.website.extract import extract_text_from_url
from backend.website.summarize import summarize_with_openai
from backend.website.document import generate_website_docx

from backend.drive_ops import upload_file_to_drive, download_file_from_drive_url
from backend.sheet_ops import update_row_values, append_todos_to_output

_HTTP_LINK_RE = re.compile(r"https?://[^\s,]+", re.IGNORECASE)


def _parse_audio_links(cell_value: str) -> List[str]:
    """
    Accepts:
      - 'https://.../d/IDa/view, https://.../d/IDb/view'
      - '(https://... , https://...)' (legacy)
      - single link
    Returns a list of URLs.
    """
    if not cell_value:
        return []
    v = str(cell_value).strip()
    if v.startswith("(") and v.endswith(")"):
        v = v[1:-1].strip()
    links = _HTTP_LINK_RE.findall(v)
    if not links and "," in v:
        links = [x.strip() for x in v.split(",") if x.strip()]
    return links


def _save_stream_to_path(stream, path: str):
    stream.seek(0)
    with open(path, "wb") as f:
        f.write(stream.read())


def _gs_hyperlink(url: str, text: str) -> str:
    if not url:
        return text or ""
    safe_url = url.replace('"', '""')
    safe_text = (text or "").replace('"', '""')
    return f'=HYPERLINK("{safe_url}","{safe_text}")'


def process_row(row_idx: int, row_data: list):
    """
    row_data columns used (1-based sheet headers -> 0-based list):
      [1]=Meeting Date (dd-mm-YYYY)
      [2]=Client Name
      [4]=Submitted By (Employee Name)
      [5]=Email ID (Employee Email)
      [6]=Meeting Audio Link(s)
      [7]=Website Link

    Behavior:
      - If multiple audio links: download all, transcribe all, CONCAT transcripts, summarize ONCE.
      - Generate exactly ONE set of docs (Meeting Notes, MoM, Action Points).
      - Push each To-Do from summary to Output sheet as a separate row (Timestamp, Task ID, Task Description,
        Employee Name/Email, Client Name, Source Link). We do NOT touch the Output sheet's "Status" column.
    """
    meeting_date = row_data[1]
    client_name = row_data[2]
    employee_name = row_data[4] if len(row_data) > 4 else ""
    employee_email = row_data[5] if len(row_data) > 5 else ""
    meeting_audio_cell = row_data[6]
    website_link = row_data[7]

    # Prepare output cells for Main sheet
    meeting_summary_cell = ""
    mom_summary_cell = ""
    action_points_cell = ""
    website_summary_cell = ""

    # ---------- AUDIO PIPELINE (merge multiple files) ----------
    audio_links = _parse_audio_links(meeting_audio_cell)
    combined_transcript = ""

    if audio_links:
        for i, link in enumerate(audio_links, start=1):
            with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp_audio:
                print(f"🎧 Downloading audio {i}/{len(audio_links)}...")
                download_file_from_drive_url(link, tmp_audio.name)
                print(f"📝 Transcribing audio {i}/{len(audio_links)}...")
                transcript = transcribe_audio(tmp_audio.name)
                combined_transcript += (transcript.strip() + "\n\n")

        # Summarize ONCE for the combined transcript
        print("🧠 Generating unified summary from combined transcript...")
        meeting_summary = generate_summary(combined_transcript)

        base = f"{client_name}_{meeting_date}"

        # Full "Meeting Notes"
        meeting_notes_stream = generate_docx(meeting_summary, client_name, meeting_date, mode="full")
        meeting_filename = f"{base}_Meeting Notes.docx"
        meeting_path = os.path.join(tempfile.gettempdir(), meeting_filename)
        _save_stream_to_path(meeting_notes_stream, meeting_path)
        meeting_url = upload_file_to_drive(meeting_path, AUDIO_DRIVE_FOLDER_ID)
        meeting_summary_cell = _gs_hyperlink(meeting_url, meeting_filename)

        # ---- Push To-Dos to Output sheet (one row per item) ----
        try:
            todos = (meeting_summary or {}).get("todo_list") or []
            if todos:
                # Old: append_todos_to_output(output_sheet, todos, meta)
                from backend.sheet_ops import append_todos_simple
                append_todos_simple(todos)
            print(
                f"🧪 OUTPUT_SHEET_ID={OUTPUT_SHEET_ID} tab={OUTPUT_SHEET_TAB} "
                f"has_output_sheet={'yes' if output_sheet else 'no'} todos={len(todos)}"
            )
            if isinstance(todos, list) and len(todos) > 0 and output_sheet is not None:
                meta = {
                    "employee_name": employee_name,
                    "employee_email": employee_email,
                    "client_name": client_name,
                    "source_link": meeting_url,  # goes to 'Source Link' column in Output sheet
                }
                append_todos_to_output(output_sheet, todos, meta)
                print(f"🧾 Pushed {len(todos)} To-Do item(s) to Output sheet.")
            elif not todos:
                print("ℹ️ No To-Do items found in summary; skipping Output sheet append.")
            elif output_sheet is None:
                print("⚠️ Output sheet handle is None (bad ID/tab or no access); skipping append.")
        except Exception as e:
            print(f"⚠️ Failed to append To-Dos to Output sheet: {e}")

        # MoM Summary
        mom_stream = generate_docx(meeting_summary, client_name, meeting_date, mode="mom")
        mom_filename = f"{base}_MoM Summary.docx"
        mom_path = os.path.join(tempfile.gettempdir(), mom_filename)
        _save_stream_to_path(mom_stream, mom_path)
        mom_url = upload_file_to_drive(mom_path, MOM_FOLDER_ID)
        mom_summary_cell = _gs_hyperlink(mom_url, mom_filename)

        # Action Points Summary
        action_stream = generate_docx(meeting_summary, client_name, meeting_date, mode="action")
        action_filename = f"{base}_Action Points Summary.docx"
        action_path = os.path.join(tempfile.gettempdir(), action_filename)
        _save_stream_to_path(action_stream, action_path)
        action_url = upload_file_to_drive(action_path, ACTION_POINT_FOLDER_ID)
        action_points_cell = _gs_hyperlink(action_url, action_filename)

    # ---------- WEBSITE PIPELINE ----------
    if website_link and str(website_link).strip():
        page_text = extract_text_from_url(website_link.strip())
        website_summary = summarize_with_openai(page_text)
        website_stream = generate_website_docx(website_summary, client_name, meeting_date)
        website_filename = f"{client_name}_{meeting_date}_Website Summary.docx"
        website_path = os.path.join(tempfile.gettempdir(), website_filename)
        _save_stream_to_path(website_stream, website_path)
        website_url = upload_file_to_drive(website_path, WEBSITE_DRIVE_FOLDER_ID)
        website_summary_cell = _gs_hyperlink(website_url, website_filename)
    else:
        website_summary_cell = "NA"

    # ---------- Write back to the Main sheet ----------
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
