from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from config import GOOGLE_SA_FILE, GOOGLE_DRIVE_SCOPES, WEBSITE_DRIVE_FOLDER_ID


def authenticate_google_drive():
    if not GOOGLE_SA_FILE:
        raise ValueError("⚠️ GOOGLE_SA_FILE not set in .env")
    creds = Credentials.from_service_account_file(
        GOOGLE_SA_FILE, scopes=GOOGLE_DRIVE_SCOPES
    )
    return build("drive", "v3", credentials=creds)


# 📤 Upload a DOCX file from memory to Google Drive (as a Google Doc)
def upload_docx_to_gdrive(docx_stream, filename):
    service = authenticate_google_drive()

    file_metadata = {
        "name": filename,
        "parents": [WEBSITE_DRIVE_FOLDER_ID],
        "mimeType": "application/vnd.google-apps.document",  # convert to Google Doc
    }

    docx_stream.seek(0)
    docx_content = docx_stream.read()

    media = MediaInMemoryUpload(
        docx_content,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=True,
    )

    uploaded = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name",
            supportsAllDrives=True,
        )
        .execute()
    )

    print(f"✅ Uploaded to Google Drive as: {uploaded['name']} (ID: {uploaded['id']})")
    return uploaded["id"]
