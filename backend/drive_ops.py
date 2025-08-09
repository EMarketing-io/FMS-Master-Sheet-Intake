import os
from googleapiclient.http import MediaFileUpload
from config.config import drive_service


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
