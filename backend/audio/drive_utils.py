import io
import tempfile
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from config.config import GOOGLE_SA_FILE, SCOPES


def get_drive_service():
    if not GOOGLE_SA_FILE:
        raise ValueError("❌ GOOGLE_SA_FILE not set in .env")
    creds = Credentials.from_service_account_file(
        GOOGLE_SA_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def download_audio_from_drive(file_id: str) -> str:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
    downloader = MediaIoBaseDownload(temp_file, request)
    done = False

    while not done:
        status, done = downloader.next_chunk()
        print(f"Downloading audio: {int(status.progress() * 100)}%")

    temp_file.close()
    return temp_file.name


def upload_file_to_drive_in_memory(file_data: io.BytesIO | bytes, folder_id: str, final_name: str = "Summary.docx") -> str:
    service = get_drive_service()
    file_metadata = {"name": final_name, "parents": [folder_id]}

    if isinstance(file_data, bytes):
        file_stream = io.BytesIO(file_data)
    elif isinstance(file_data, io.BytesIO):
        file_stream = file_data
        file_stream.seek(0)
    else:
        raise TypeError("❌ file_data must be bytes or BytesIO")

    media = MediaIoBaseUpload(
        file_stream,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=True,
    )

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )

    print(f"📤 File uploaded: {file.get('id')}")
    return file.get("id")


def find_audio_file_in_folder(folder_id: str, extension: str = ".m4a") -> Optional[str]:
    service = get_drive_service()
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )

    for file in results.get("files", []):
        if file["name"].lower().endswith(extension.lower()):
            print(f"🎯 Found audio file: {file['name']}")
            return file["id"]

    print("⚠️ No matching audio file found in folder.")
    return None
