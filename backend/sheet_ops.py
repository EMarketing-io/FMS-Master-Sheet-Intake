from typing import List, Dict
from datetime import datetime
from pytz import timezone
import uuid
import gspread
from config.config import OUTPUT_SHEET_ID

def update_row_values(sheet_obj, row_number: int, updates: dict):
    """Update specific columns in a row by header name."""
    headers = sheet_obj.row_values(1)
    for col_name, new_value in updates.items():
        if col_name in headers:
            col_index = headers.index(col_name) + 1
            sheet_obj.update_cell(row_number, col_index, new_value)

def _hdr_first_idx(headers: List[str], name: str) -> int:
    """Case-insensitive first index; returns -1 if not found."""
    low = [h.strip().lower() for h in headers]
    try:
        return low.index(name.strip().lower())
    except ValueError:
        return -1

def _hdr_all_idx(headers: List[str], name: str) -> List[int]:
    """All case-insensitive indices (for duplicate header names like 'Timestamp')."""
    low = [h.strip().lower() for h in headers]
    return [i for i, h in enumerate(low) if h == name.strip().lower()]

def _ensure_headers(ws: gspread.Worksheet) -> List[str]:
    """If header row is empty, create the 17-column header."""
    expected = [
        "Timestamp", "Task ID", "Task Description", "Employee Name", "Employee Email ID",
        "Target Date", "Priority", "Approval Needed", "Client Name", "Department",
        "Assigned Name", "Assigned Email ID", "Comments", "Source Link", "Checkbox",
        "Timestamp", "Status",
    ]
    headers = ws.row_values(1)
    if not any(h.strip() for h in headers):
        ws.update("A1:Q1", [expected])  # A..Q is 17 columns
        return expected
    return headers

def append_todos_to_output(
    output_ws,
    todos: List[str],
    meta: Dict[str, str],
):
    if output_ws is None:
        print("⚠️ Output worksheet handle is None.")
        return
    if not todos:
        print("ℹ️ No To-Do items to append.")
        return

    headers: List[str] = _ensure_headers(output_ws)
    ncols = max(len(headers), 17)

    # Column indices (0-based)
    idx_ts_all       = _hdr_all_idx(headers, "Timestamp")     # could be [0, 15]
    idx_task_id      = _hdr_first_idx(headers, "Task ID")
    idx_desc         = _hdr_first_idx(headers, "Task Description")
    idx_emp_name     = _hdr_first_idx(headers, "Employee Name")
    idx_emp_email    = _hdr_first_idx(headers, "Employee Email ID")
    idx_client       = _hdr_first_idx(headers, "Client Name")
    idx_src          = _hdr_first_idx(headers, "Source Link")
    # NOTE: No Status column write — removed as requested.

    # Use the first "Timestamp" only (the created-at column)
    idx_created_ts = idx_ts_all[0] if idx_ts_all else -1

    ist_now = datetime.now(timezone("Asia/Kolkata")).strftime("%d/%m/%Y %H:%M:%S")

    rows: List[List[str]] = []
    for todo in todos:
        if not todo or not str(todo).strip():
            continue
        row = [""] * ncols
        if idx_created_ts >= 0: row[idx_created_ts] = ist_now
        if idx_task_id   >= 0: row[idx_task_id]     = uuid.uuid4().hex[:8]
        if idx_desc      >= 0: row[idx_desc]        = str(todo).strip()
        if idx_emp_name  >= 0: row[idx_emp_name]    = meta.get("employee_name", "")
        if idx_emp_email >= 0: row[idx_emp_email]   = meta.get("employee_email", "")
        if idx_client    >= 0: row[idx_client]      = meta.get("client_name", "")
        if idx_src       >= 0: row[idx_src]         = meta.get("source_link", "")
        rows.append(row)

    if not rows:
        print("ℹ️ All To-Do items were empty after trimming; nothing to append.")
        return

    try:
        output_ws.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"✅ Appended {len(rows)} To-Do rows to Output sheet.")
    except Exception as e:
        print(f"❌ Failed to append To-Do rows: {e}")

def append_todos_simple(todos: list):
    """Append To-Dos into the Output sheet, each in column C (Task Description)."""
    if not todos:
        print("ℹ️ No To-Do items to append.")
        return

    try:
        gc = gspread.service_account(filename="service_account.json")  # adjust path if needed
        sh = gc.open_by_key(OUTPUT_SHEET_ID)
        ws = sh.sheet1  # first sheet/tab

        # Prepare rows: empty cols A, B, D… only C gets filled
        rows = [["", "", str(todo)] for todo in todos if str(todo).strip()]

        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            print(f"✅ Appended {len(rows)} To-Do rows into column C of output sheet.")
    except Exception as e:
        print(f"❌ Failed to append To-Dos: {e}")