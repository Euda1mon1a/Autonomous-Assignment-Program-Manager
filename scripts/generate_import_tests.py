from openpyxl import Workbook
import os

def create_test_files():
    # 1. Valid Import File
    wb = Workbook()
    ws = wb.active
    ws.title = "Schedule"

    # Headers
    ws.append(["person_name", "assignment_date", "rotation_name", "slot"])

    # Data
    ws.append(["resident_0", "2026-02-01", "Internal Medicine", "AM"])
    ws.append(["resident_1", "2026-02-01", "Pediatrics", "PM"])
    ws.append(["faculty_0", "2026-02-02", "Clinic", "AM"])

    valid_path = "/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/valid_import.xlsx"
    wb.save(valid_path)
    print(f"Created {valid_path}")

    # 2. Malformed Import File (Missing required columns)
    wb_mal = Workbook()
    ws_mal = wb_mal.active
    ws_mal.append(["wrong_header", "something_else"])
    ws_mal.append(["val1", "val2"])

    malformed_path = "/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/malformed_import.xlsx"
    wb_mal.save(malformed_path)
    print(f"Created {malformed_path}")

if __name__ == "__main__":
    create_test_files()
