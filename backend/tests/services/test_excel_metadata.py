import json
from openpyxl import Workbook
from app.services.excel_metadata import (
    ExportMetadata,
    write_sys_meta_sheet,
    write_ref_sheet,
    read_sys_meta,
    read_ref_codes,
    compute_row_hash,
    normalize_for_hash,
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


def test_normalize_for_hash_none_and_empty():
    assert normalize_for_hash(None) == ""
    assert normalize_for_hash("") == ""
    assert normalize_for_hash("  ") == ""


def test_normalize_for_hash_strips_and_uppercases():
    assert normalize_for_hash("  cli  ") == "CLI"
    assert normalize_for_hash("surg") == "SURG"
    assert normalize_for_hash("NF") == "NF"


def test_normalize_for_hash_removes_trailing_dot_zero():
    """Excel renders integer-like floats as '1.0' — should normalize to '1'."""
    assert normalize_for_hash("1.0") == "1"
    assert normalize_for_hash(1.0) == "1"
    assert normalize_for_hash("10.0") == "10"


def test_normalize_for_hash_preserves_real_decimals():
    assert normalize_for_hash("1.5") == "1.5"
    assert normalize_for_hash("0.75") == "0.75"


def test_normalize_for_hash_idempotent():
    """Double-normalization should produce the same result."""
    values = [None, "", "  cli  ", "SURG", "1.0", 1.0, "NF"]
    for v in values:
        once = normalize_for_hash(v)
        twice = normalize_for_hash(once)
        assert once == twice, f"Not idempotent for {v!r}: {once!r} != {twice!r}"


def test_compute_row_hash_symmetric():
    """Export JSON values and Excel cell values should produce the same hash.

    Simulates: export writes 'CLI' as string, Excel reads it back as 'CLI'
    or ' CLI ' with whitespace.
    """
    export_hash = compute_row_hash("uuid-1", "SURG", None, ["CLI", "OR", None, "NF"])
    import_hash = compute_row_hash(
        "uuid-1", " surg ", None, [" cli ", "or", None, "nf"]
    )
    assert export_hash == import_hash


def test_compute_row_hash_float_coercion():
    """Excel may coerce integer activity codes to floats."""
    export_hash = compute_row_hash("uuid-1", "SURG", None, ["1", "2", None])
    import_hash = compute_row_hash("uuid-1", "SURG", None, ["1.0", "2.0", None])
    assert export_hash == import_hash
