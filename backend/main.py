import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config import sheet
from backend.processor import process_row

CHECK_INTERVAL = 10


def find_processing_rows(sheet_obj):
    all_values = sheet_obj.get_all_values()
    if not all_values:
        return []

    header = all_values[0]
    status_idx = header.index("Status")
    processing_rows = []

    for i, row in enumerate(all_values[1:], start=2): 
        if len(row) > status_idx:
            status_val = row[status_idx].strip().lower()
            if status_val == "processing":
                processing_rows.append((i, row))

    return processing_rows


if __name__ == "__main__":
    while True:
        rows_to_process = find_processing_rows(sheet)

        if rows_to_process:
            print(f"🔍 Found {len(rows_to_process)} row(s) with Status = 'Processing'")
            for row_idx, row_data in rows_to_process:
                try:
                    process_row(row_idx, row_data)
                except Exception as e:
                    print(f"❌ Error processing row {row_idx}: {e}")
        
        else:
            print("✅ No rows with Status = 'Processing' found.")

        print(f"⏳ Waiting {CHECK_INTERVAL} seconds before checking again...\n")
        time.sleep(CHECK_INTERVAL)