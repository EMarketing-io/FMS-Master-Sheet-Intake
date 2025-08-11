from typing import List
from datetime import datetime
from pytz import timezone

def update_row_values(sheet_obj, row_number: int, updates: dict):
    """Update specific columns in a row by header name."""
    headers = sheet_obj.row_values(1)
    for col_name, new_value in updates.items():
        if col_name in headers:
            col_index = headers.index(col_name) + 1
            sheet_obj.update_cell(row_number, col_index, new_value)

def _hdr_index(headers: List[str], name: str) -> int:
    """Case-insensitive header lookup; returns -1 if not found."""
    low = [h.strip().lower() for h in headers]
    try:
        return low.index(name.strip().lower())
    except ValueError:
        return -1

def append_todos_to_output(output_ws, todos: List[str], client_name: str, source_link: str):
    """
    Append one row per To-Do into the output worksheet.

    Expected headers (case-insensitive):
      - Timestamp
      - Task ID
      - Task Description
      - Client Name
      - Source Link

    Any missing headers are ignored (cells left blank).
    Timestamp is IST now (dd/mm/YYYY HH:MM:SS).
    Task ID is a short random hex (8 chars).
    """
    if not output_ws or not todos:
        return

    headers: List[str] = output_ws.row_values(1)
    ncols = len(headers)

    col_ts = _hdr_index(headers, "Timestamp")
    col_tid = _hdr_index(headers, "Task ID")
    col_desc = _hdr_index(headers, "Task Description")
    col_client = _hdr_index(headers, "Client Name")
    col_src = _hdr_index(headers, "Source Link")

    ist_now = datetime.now(timezone("Asia/Kolkata")).strftime("%d/%m/%Y %H:%M:%S")

    rows: List[List[str]] = []
    import uuid

    for todo in todos:
        if not todo or not str(todo).strip():
            continue
        row = [""] * max(ncols, 20)  # ensure enough columns; will slice back to header length
        if col_ts >= 0: row[col_ts] = ist_now
        if col_tid >= 0: row[col_tid] = uuid.uuid4().hex[:8]
        if col_desc >= 0: row[col_desc] = str(todo).strip()
        if col_client >= 0: row[col_client] = client_name
        if col_src >= 0: row[col_src] = source_link
        rows.append(row[:ncols] if ncols else row)

    if rows:
        # Batch append for speed
        output_ws.append_rows(rows, value_input_option="USER_ENTERED")
