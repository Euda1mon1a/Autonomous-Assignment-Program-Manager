import json
from openpyxl import Workbook
from app.services.excel_metadata import (
    ExportMetadata,
    write_sys_meta_sheet,
    write_ref_sheet,
    read_sys_meta,
    read_ref_codes,
    compute_row_hash,
)


def test_sys_meta_roundtrip():
    wb = Workbook()
    meta = ExportMetadata(
        academic_year=2026,
        block_number=10,
        export_timestamp="2026-02-24T10:30:00Z",
        export_version=1,
    )

    write_sys_meta_sheet(wb, meta)

    assert "__SYS_META__" in wb.sheetnames
    assert wb["__SYS_META__"].sheet_state == "veryHidden"

    read_meta = read_sys_meta(wb)

    assert read_meta is not None
    assert read_meta.academic_year == 2026
    assert read_meta.block_number == 10
    assert read_meta.export_timestamp == "2026-02-24T10:30:00Z"
    assert read_meta.export_version == 1


def test_sys_meta_legacy():
    wb = Workbook()
    read_meta = read_sys_meta(wb)
    assert read_meta is None


def test_ref_sheet_roundtrip():
    wb = Workbook()
    rotations = ["SURG", "MED", "PEDS"]
    activities = ["CLI", "OR", "LV"]

    write_ref_sheet(wb, rotations, activities)

    assert "__REF__" in wb.sheetnames
    assert wb["__REF__"].sheet_state == "veryHidden"

    # Check named ranges
    assert "ValidRotations" in wb.defined_names
    assert "ValidActivities" in wb.defined_names

    ref = read_ref_codes(wb)
    assert ref["rotations"] == sorted(rotations)
    assert ref["activities"] == sorted(activities)


def test_compute_row_hash():
    hash1 = compute_row_hash("uuid-123", "SURG", None, ["CLI", "OR", None])
    hash2 = compute_row_hash("uuid-123", "SURG", None, ["CLI", "OR", None])
    hash3 = compute_row_hash("uuid-123", "MED", None, ["CLI", "OR", None])

    assert hash1 == hash2
    assert hash1 != hash3
