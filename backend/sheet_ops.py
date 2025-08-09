from config.config import sheet


def update_row_values(sheet_obj, row_number: int, updates: dict):
    headers = sheet_obj.row_values(1)
    for col_name, new_value in updates.items():
        if col_name in headers:
            col_index = headers.index(col_name) + 1
            sheet_obj.update_cell(row_number, col_index, new_value)
