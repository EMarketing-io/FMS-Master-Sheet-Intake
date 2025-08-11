import io
import os
import re
import time
from typing import Optional
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
from config.config import drive_service

_FILE_ID_RE = re.compile(r"/file/d/([^/]+)/")

def extract_file_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    m = _FILE_ID_RE.search(url)
    return m.group(1) if m else None

def download_file_from_drive_url(drive_url: str, dest_path: str, max_retries: int = 5) -> None:
    """
    Downloads a Drive file given its typical webViewLink like:
    https://drive.google.com/file/d/<ID>/view
    Uses MediaIoBaseDownload (Drive API) to avoid SSL EOF issues.
    """
    file_id = extract_file_id_from_url(drive_url) or drive_url  # allow raw id too
    request = drive_service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        attempt = 0
        while not done:
            try:
                status, done = downloader.next_chunk()
                if status:
                    print(f"⬇️  Download {int(status.progress() * 100)}%")
            except (HttpError, OSError) as e:
                attempt += 1
                if attempt >= max_retries:
                    try:
                        fh.flush()
                        os.fsync(fh.fileno())
                    except Exception:
                        pass
                    raise RuntimeError(f"❌ Drive download failed after {max_retries} attempts: {e}")
                wait = 2 ** attempt
                print(f"⚠️ Download error: {e} — retrying in {wait}s...")
                time.sleep(wait)

def upload_file_to_drive(file_path: str, parent_folder_id: str) -> str:
    file_metadata = {"name": os.path.basename(file_path), "parents": [parent_folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    file = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id", supportsAllDrives=True)
        .execute()
    )
    file_id = file.get("id")
    return f"https://drive.google.com/file/d/{file_id}/view"
