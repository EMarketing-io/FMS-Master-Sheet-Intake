import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config import sheet
from backend.processor import process_row
import time



def get_processing_rows():
    all_values = sheet.get_all_records()
    rows = []
    for idx, row in enumerate(all_values, start=2):
        if row.get("Status", "").strip().lower() == "processing":
            rows.append((idx, row))
    return rows


if __name__ == "__main__":
    while True:
        rows = get_processing_rows()
        if not rows:
            print("✅ No rows with Status = 'Processing'. Processes Ended.")
            break  # Exit script

        print(f"🔍 Found {len(rows)} row(s) with Status = 'Processing'")
        for idx, row_data in rows:
            try:
                process_row(idx, list(row_data.values()))
            except Exception as e:
                print(f"❌ Error processing row {idx}: {e}")
                # optional: update status to "Error" here

        # After processing current batch, check again before deciding to sleep
        rows_left = get_processing_rows()
        if not rows_left:
            print("✅ All rows processed. Stopping backend.")
            break

        print("⏳ Waiting 10 seconds before checking again...")
        time.sleep(10)
