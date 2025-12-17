# FMIT Scheduling - Parallel Development Sessions

## Overview
This document defines 5 parallel terminal sessions with **zero file overlap**.
Each session owns specific files and must not modify files owned by other sessions.

---

## Session Allocation Matrix

| Terminal | Branch Suffix | Primary Focus | Key Files |
|----------|---------------|---------------|-----------|
| T1 | `-tests-unit` | All unit tests in test_fmit_scheduling.py | test_fmit_scheduling.py, conftest.py |
| T2 | `-tests-cli` | CLI tool tests | test_cli_swap_analyzer.py (NEW) |
| T3 | `-tests-integration` | Integration workflow tests | test_fmit_swap_workflow.py (NEW) |
| T4 | `-tests-performance` | Performance benchmarks | test_fmit_performance.py (NEW) |
| T5 | `-tests-xlsx` | xlsx_import coverage | test_xlsx_import_coverage.py (NEW) |

---

## Terminal 1: Unit Tests (test_fmit_scheduling.py)

**Branch:** `claude/fmit-tests-unit-{SESSION_ID}`

### Files OWNED (only modify these):
- `backend/tests/test_fmit_scheduling.py` (ENTIRE FILE)
- `backend/tests/conftest.py` (test fixtures only)
- `backend/pytest.ini` (if needed)

### Files DO NOT MODIFY:
- Any files in `backend/app/`
- Any other test files
- `backend/tests/integration/*`

### Task:
1. Ensure pytest can discover and run tests
2. Fix any import/dependency issues
3. Run and fix ALL test classes in test_fmit_scheduling.py:
   - TestBackToBackDetection (6 tests)
   - TestAlternatingPatternDetection (4 tests)
   - TestScheduleFlexibility (4 tests)
   - TestSwapFinder (5 tests)
   - TestAbsenceIntegration (4 tests)
   - TestSwapFinderAPI (5 tests)
   - TestSwapFinderSchemas (3 tests)

### Success Criteria:
```bash
pytest backend/tests/test_fmit_scheduling.py -v
# All 31 tests should pass
```

### Notes:
- If fixtures are missing, add them to conftest.py
- Do NOT modify the source code in app/ - only fix tests
- Document any test data assumptions

---

## Terminal 2: CLI Tests (NEW FILE)

**Branch:** `claude/fmit-tests-cli-{SESSION_ID}`

### Files OWNED (only modify these):
- `backend/tests/test_cli_swap_analyzer.py` (CREATE NEW)

### Files DO NOT MODIFY:
- `backend/tests/test_fmit_scheduling.py`
- `backend/tests/conftest.py`
- `backend/app/cli/swap_analyzer.py`
- Any other existing files

### Task:
Create comprehensive tests for the CLI tool at `backend/app/cli/swap_analyzer.py`:

1. Test argument parsing:
   - `--file` argument (required)
   - `--faculty` argument (optional)
   - `--week` argument (optional)
   - `--output` format options (json, table, csv)

2. Test output formatting:
   - JSON output structure
   - Table output alignment
   - CSV output headers

3. Test error handling:
   - Missing required file
   - Invalid file format
   - Faculty not found in schedule
   - Invalid date format

4. Test help output:
   - `--help` shows usage
   - All arguments documented

### Success Criteria:
```bash
pytest backend/tests/test_cli_swap_analyzer.py -v
# Minimum 8 tests, all passing
```

### Template:
```python
"""Tests for swap_analyzer CLI tool."""
import pytest
import subprocess
import json
from pathlib import Path


class TestSwapAnalyzerCLI:
    """Tests for swap_analyzer.py command-line interface."""

    @pytest.fixture
    def cli_path(self) -> Path:
        """Path to the CLI script."""
        return Path(__file__).parent.parent / "app" / "cli" / "swap_analyzer.py"

    @pytest.fixture
    def sample_excel_path(self, tmp_path) -> Path:
        """Create a sample Excel file for testing."""
        # Create minimal test Excel file
        from openpyxl import Workbook
        from datetime import date

        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Provider"
        ws["B1"] = date(2025, 3, 3)
        ws["A2"] = "Dr. Smith"
        ws["B2"] = "FMIT"

        file_path = tmp_path / "test_schedule.xlsx"
        wb.save(file_path)
        return file_path

    def test_help_output(self, cli_path):
        """CLI should display help with --help flag."""
        result = subprocess.run(
            ["python", str(cli_path), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()

    def test_missing_file_error(self, cli_path):
        """CLI should error when file doesn't exist."""
        result = subprocess.run(
            ["python", str(cli_path), "--file", "nonexistent.xlsx"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    # Add more tests...
```

---

## Terminal 3: Integration Tests (NEW FILE)

**Branch:** `claude/fmit-tests-integration-{SESSION_ID}`

### Files OWNED (only modify these):
- `backend/tests/integration/test_fmit_swap_workflow.py` (CREATE NEW)

### Files DO NOT MODIFY:
- `backend/tests/test_fmit_scheduling.py`
- `backend/tests/integration/test_scheduling_flow.py`
- `backend/tests/integration/conftest.py`
- `backend/tests/conftest.py`
- Any files in `backend/app/`

### Task:
Create end-to-end integration test for the FMIT swap workflow:

1. **Upload Excel Schedule Test**
   - POST Excel file to /api/schedule/swaps/find
   - Verify schedule is parsed correctly
   - Check provider extraction

2. **Find Swap Candidates Test**
   - Request candidates for specific faculty/week
   - Verify candidate list structure
   - Check back-to-back conflict detection
   - Verify external conflict flagging

3. **Full Workflow Test**
   - Upload schedule → Find candidates → Verify constraints
   - Test with realistic multi-provider schedule

4. **Error Handling Tests**
   - Invalid Excel format
   - Missing required fields
   - Faculty not in schedule

### Success Criteria:
```bash
pytest backend/tests/integration/test_fmit_swap_workflow.py -v
# Minimum 5 tests, all passing
```

### Template:
```python
"""Integration tests for FMIT swap workflow."""
import pytest
import io
from datetime import date
from fastapi.testclient import TestClient
from openpyxl import Workbook


class TestFMITSwapWorkflow:
    """End-to-end tests for FMIT swap finding workflow."""

    @pytest.fixture
    def realistic_schedule_bytes(self) -> bytes:
        """Create a realistic FMIT schedule Excel file."""
        wb = Workbook()
        ws = wb.active

        # Header with dates (6 weeks)
        ws["A1"] = "Provider"
        base_date = date(2025, 3, 3)
        for i in range(6):
            col = chr(ord('B') + i)
            ws[f"{col}1"] = base_date.replace(day=base_date.day + i * 7)

        # Multiple providers with different patterns
        providers = [
            ("Dr. Smith", ["FMIT", "", "FMIT", "", "FMIT", ""]),      # Alternating
            ("Dr. Jones", ["", "FMIT", "", "", "FMIT", ""]),          # Sparse
            ("Dr. Lee", ["", "", "", "FMIT", "", ""]),                # Single week
            ("Dr. Brown", ["FMIT", "FMIT", "", "", "", ""]),          # Back-to-back
        ]

        for row_idx, (name, weeks) in enumerate(providers, start=2):
            ws[f"A{row_idx}"] = name
            for col_idx, value in enumerate(weeks):
                col = chr(ord('B') + col_idx)
                ws[f"{col}{row_idx}"] = value

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    def test_full_swap_workflow(
        self,
        client: TestClient,
        realistic_schedule_bytes: bytes,
    ):
        """Test complete workflow: upload → find → verify."""
        import json

        # Step 1: Find swap candidates
        request_data = {
            "target_faculty": "Dr. Smith",
            "target_week": "2025-03-03",
            "include_absence_conflicts": False,
        }

        response = client.post(
            "/api/schedule/swaps/find",
            files={"fmit_file": ("schedule.xlsx", realistic_schedule_bytes)},
            data={"request_json": json.dumps(request_data)},
        )

        assert response.status_code == 200
        data = response.json()

        # Step 2: Verify response structure
        assert data["success"]
        assert data["target_faculty"] == "Dr. Smith"
        assert "candidates" in data

        # Step 3: Verify constraint detection
        # Dr. Brown has back-to-back weeks, should be flagged
        brown_candidate = next(
            (c for c in data["candidates"] if c["faculty"] == "Dr. Brown"),
            None
        )
        if brown_candidate:
            # Taking week 1 would create back-to-back for Brown
            assert not brown_candidate.get("back_to_back_ok", True)

    # Add more tests...
```

---

## Terminal 4: Performance Tests (NEW FILE)

**Branch:** `claude/fmit-tests-performance-{SESSION_ID}`

### Files OWNED (only modify these):
- `backend/tests/test_fmit_performance.py` (CREATE NEW)

### Files DO NOT MODIFY:
- `backend/tests/test_fmit_scheduling.py`
- Any files in `backend/app/`
- Any other test files

### Task:
Create performance benchmarks for SwapFinder:

1. **Large Schedule Test**
   - 50+ faculty members
   - Full academic year (52 weeks)
   - Verify find_swap_candidates < 1 second

2. **Memory Usage Test**
   - Track memory during large schedule processing
   - Ensure no memory leaks

3. **Concurrent Request Test**
   - Multiple simultaneous swap finder requests
   - Verify no race conditions

4. **Scaling Test**
   - Measure performance at 10, 25, 50, 100 faculty
   - Document scaling characteristics

### Success Criteria:
```bash
pytest backend/tests/test_fmit_performance.py -v
# All performance benchmarks pass
# find_swap_candidates < 1s for 50 faculty
```

### Template:
```python
"""Performance tests for FMIT scheduling."""
import pytest
import time
from datetime import date, timedelta
from app.services.xlsx_import import (
    SwapFinder,
    ImportResult,
    ProviderSchedule,
    ScheduleSlot,
    SlotType,
)


class TestSwapFinderPerformance:
    """Performance benchmarks for SwapFinder."""

    def generate_large_schedule(self, num_faculty: int, num_weeks: int) -> ImportResult:
        """Generate a large test schedule."""
        result = ImportResult(success=True)
        base_date = date(2025, 1, 6)  # First Monday of 2025

        for i in range(num_faculty):
            provider_name = f"Dr. Faculty{i:03d}"
            provider = ProviderSchedule(name=provider_name)

            # Assign ~6 FMIT weeks per faculty (distributed)
            assigned_weeks = [
                (i * 7 + j * num_faculty) % num_weeks
                for j in range(6)
            ]

            for week_num in assigned_weeks:
                week_start = base_date + timedelta(weeks=week_num)
                for day in range(5):  # Mon-Fri
                    for tod in ["AM", "PM"]:
                        slot = ScheduleSlot(
                            provider_name=provider_name,
                            date=week_start + timedelta(days=day),
                            time_of_day=tod,
                            slot_type=SlotType.FMIT,
                            raw_value="FMIT",
                        )
                        provider.add_slot(slot)

            result.providers[provider_name] = provider

        return result

    def test_find_candidates_under_one_second(self):
        """SwapFinder should complete in < 1s for 50 faculty."""
        schedule = self.generate_large_schedule(num_faculty=50, num_weeks=52)
        finder = SwapFinder(fmit_schedule=schedule)

        # Pick a faculty and week to search
        target_faculty = "Dr. Faculty000"
        target_week = date(2025, 1, 6)

        start = time.perf_counter()
        candidates = finder.find_swap_candidates(target_faculty, target_week)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"find_swap_candidates took {elapsed:.2f}s (limit: 1s)"
        assert len(candidates) > 0  # Should find some candidates

    @pytest.mark.parametrize("num_faculty", [10, 25, 50, 100])
    def test_scaling_characteristics(self, num_faculty: int):
        """Document scaling behavior at different sizes."""
        schedule = self.generate_large_schedule(num_faculty=num_faculty, num_weeks=52)
        finder = SwapFinder(fmit_schedule=schedule)

        target_faculty = "Dr. Faculty000"
        target_week = date(2025, 1, 6)

        start = time.perf_counter()
        candidates = finder.find_swap_candidates(target_faculty, target_week)
        elapsed = time.perf_counter() - start

        # Log for documentation
        print(f"\n{num_faculty} faculty: {elapsed:.3f}s, {len(candidates)} candidates")

        # Reasonable limits based on faculty count
        limit = num_faculty * 0.05  # 50ms per faculty max
        assert elapsed < limit, f"Scaling issue: {elapsed:.2f}s for {num_faculty} faculty"

    # Add more tests...
```

---

## Terminal 5: xlsx_import Coverage Tests (NEW FILE)

**Branch:** `claude/fmit-tests-xlsx-{SESSION_ID}`

### Files OWNED (only modify these):
- `backend/tests/test_xlsx_import_coverage.py` (CREATE NEW)

### Files DO NOT MODIFY:
- `backend/tests/test_fmit_scheduling.py`
- `backend/app/services/xlsx_import.py`
- Any other existing files

### Task:
Add tests to achieve 80%+ coverage for xlsx_import.py:

1. **ClinicScheduleImporter Tests**
   - Parse valid Excel files
   - Handle malformed Excel files
   - Extract provider names correctly
   - Handle empty cells

2. **SlotType Classification Tests**
   - FMIT detection from various formats ("FMIT", "fmit", "F.M.I.T.")
   - CLINIC detection
   - OFF detection
   - Unknown value handling

3. **Date Parsing Tests**
   - Standard date formats
   - Excel serial date numbers
   - Invalid date handling
   - Timezone considerations

4. **ProviderSchedule Tests**
   - Adding slots
   - Getting weeks
   - Filtering by slot type

### Success Criteria:
```bash
pytest backend/tests/test_xlsx_import_coverage.py -v --cov=app.services.xlsx_import --cov-report=term-missing
# Coverage should be 80%+
```

### Template:
```python
"""Coverage tests for xlsx_import module."""
import pytest
from datetime import date, datetime
from app.services.xlsx_import import (
    ClinicScheduleImporter,
    SlotType,
    ScheduleSlot,
    ProviderSchedule,
    ImportResult,
    classify_slot_type,
)


class TestSlotTypeClassification:
    """Tests for slot type classification logic."""

    @pytest.mark.parametrize("raw_value,expected", [
        ("FMIT", SlotType.FMIT),
        ("fmit", SlotType.FMIT),
        ("F.M.I.T.", SlotType.FMIT),
        ("Fmit", SlotType.FMIT),
        ("CLINIC", SlotType.CLINIC),
        ("Clinic", SlotType.CLINIC),
        ("OFF", SlotType.OFF),
        ("off", SlotType.OFF),
        ("PTO", SlotType.OFF),
        ("", SlotType.EMPTY),
        (None, SlotType.EMPTY),
        ("UNKNOWN", SlotType.OTHER),
    ])
    def test_classify_slot_type(self, raw_value: str, expected: SlotType):
        """Should correctly classify various slot values."""
        result = classify_slot_type(raw_value)
        assert result == expected


class TestProviderSchedule:
    """Tests for ProviderSchedule class."""

    def test_add_slot(self):
        """Should add slots correctly."""
        provider = ProviderSchedule(name="Dr. Test")
        slot = ScheduleSlot(
            provider_name="Dr. Test",
            date=date(2025, 3, 3),
            time_of_day="AM",
            slot_type=SlotType.FMIT,
            raw_value="FMIT",
        )
        provider.add_slot(slot)

        assert len(provider.slots) == 1
        assert provider.slots[0] == slot

    def test_get_fmit_weeks(self):
        """Should return unique FMIT weeks."""
        provider = ProviderSchedule(name="Dr. Test")

        # Add slots for same week (Mon-Fri)
        for day in range(5):
            for tod in ["AM", "PM"]:
                slot = ScheduleSlot(
                    provider_name="Dr. Test",
                    date=date(2025, 3, 3) + timedelta(days=day),
                    time_of_day=tod,
                    slot_type=SlotType.FMIT,
                    raw_value="FMIT",
                )
                provider.add_slot(slot)

        weeks = provider.get_fmit_weeks()
        assert len(weeks) == 1  # All slots in same week
        assert weeks[0] == date(2025, 3, 3)


class TestClinicScheduleImporter:
    """Tests for ClinicScheduleImporter class."""

    @pytest.fixture
    def sample_excel_bytes(self) -> bytes:
        """Create sample Excel file."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Provider"
        ws["B1"] = date(2025, 3, 3)
        ws["A2"] = "Dr. Test"
        ws["B2"] = "FMIT"

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    def test_import_valid_excel(self, sample_excel_bytes: bytes):
        """Should successfully import valid Excel file."""
        import io
        importer = ClinicScheduleImporter()
        result = importer.import_schedule(io.BytesIO(sample_excel_bytes))

        assert result.success
        assert "Dr. Test" in result.providers

    # Add more tests...
```

---

## Execution Order

### Phase 1: All 5 Terminals in Parallel (No Dependencies)
```
T1: pytest backend/tests/test_fmit_scheduling.py -v
T2: Create + run test_cli_swap_analyzer.py
T3: Create + run test_fmit_swap_workflow.py
T4: Create + run test_fmit_performance.py
T5: Create + run test_xlsx_import_coverage.py
```

### Phase 2: Verify All Tests Pass
```bash
# Run all tests together
pytest backend/tests/test_fmit_scheduling.py \
       backend/tests/test_cli_swap_analyzer.py \
       backend/tests/integration/test_fmit_swap_workflow.py \
       backend/tests/test_fmit_performance.py \
       backend/tests/test_xlsx_import_coverage.py \
       -v
```

---

## File Ownership Summary

| File | Owner Terminal | Status |
|------|----------------|--------|
| `backend/tests/test_fmit_scheduling.py` | T1 | Existing - Fix |
| `backend/tests/conftest.py` | T1 | Existing - May modify |
| `backend/tests/test_cli_swap_analyzer.py` | T2 | CREATE NEW |
| `backend/tests/integration/test_fmit_swap_workflow.py` | T3 | CREATE NEW |
| `backend/tests/test_fmit_performance.py` | T4 | CREATE NEW |
| `backend/tests/test_xlsx_import_coverage.py` | T5 | CREATE NEW |

**CRITICAL**: Each terminal must ONLY modify files in its OWNED list.
Any modification to files outside the owned list will cause merge conflicts.

---

## Git Workflow for Each Terminal

```bash
# 1. Create branch
git checkout -b claude/fmit-tests-{type}-{SESSION_ID}

# 2. Make changes to OWNED files only

# 3. Commit with descriptive message
git add backend/tests/{owned_file}.py
git commit -m "test: add/fix {description}

- Specific change 1
- Specific change 2"

# 4. Push to remote
git push -u origin claude/fmit-tests-{type}-{SESSION_ID}
```

---

## Verification Checklist

Before completing each session:

- [ ] All owned tests pass locally
- [ ] No modifications to files outside OWNED list
- [ ] Code follows existing test patterns
- [ ] Fixtures are self-contained (don't rely on other sessions)
- [ ] Committed and pushed to correct branch
