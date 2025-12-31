# Review Patches for Claude (Session 14 - Scheduling + Airtable)

This document proposes concrete fixes for issues found in the latest code changes.

## 1) Block `block_half` should scope to the correct academic year

Problem: `block_half` uses the earliest date for a given `block_number` across *all years*, so later years compute the wrong day-in-block. It also hardcodes 28 days.

Suggested approach: compute the academic-year window for the block date and query the first block date *within that window*, using `BLOCK_LENGTH_DAYS` for half calculations.

```diff
diff --git a/backend/app/models/block.py b/backend/app/models/block.py
--- a/backend/app/models/block.py
+++ b/backend/app/models/block.py
@@
     def block_half(self) -> int:
@@
-        from sqlalchemy import func
-        from sqlalchemy.orm import object_session
+        from datetime import timedelta
+        from sqlalchemy import func
+        from sqlalchemy.orm import object_session
+        from app.core.config import get_settings
+
+        settings = get_settings()

         session = object_session(self)
         if session is None:
             # Fallback if not attached to session - use modulo of day of year
             day_of_year = self.date.timetuple().tm_yday
-            return 1 if (day_of_year % 28) < 14 else 2
+            half = settings.BLOCK_LENGTH_DAYS // 2
+            return 1 if (day_of_year % settings.BLOCK_LENGTH_DAYS) < half else 2

-        # Find the first date of this block_number
-        first_date = session.query(func.min(Block.date)).filter(
-            Block.block_number == self.block_number
-        ).scalar()
+        # Find the first date of this block_number within the same academic year
+        year = self.date.year if self.date.month >= settings.ACADEMIC_YEAR_START_MONTH else self.date.year - 1
+        academic_year_start = self.date.replace(
+            year=year,
+            month=settings.ACADEMIC_YEAR_START_MONTH,
+            day=settings.ACADEMIC_YEAR_START_DAY,
+        )
+        academic_year_end = academic_year_start + timedelta(days=365)
+
+        first_date = session.query(func.min(Block.date)).filter(
+            Block.block_number == self.block_number,
+            Block.date >= academic_year_start,
+            Block.date < academic_year_end,
+        ).scalar()
@@
-        # Calculate day within the block (0-27)
+        # Calculate day within the block (0-27)
         day_in_block = (self.date - first_date).days

         # First half = days 0-13, Second half = days 14-27
-        return 1 if day_in_block < 14 else 2
+        half = settings.BLOCK_LENGTH_DAYS // 2
+        return 1 if day_in_block < half else 2
```

## 2) Preserved FMIT assignments should block supervision assignment

Problem: preserved FMIT faculty assignments are not considered in `_assign_faculty`, so the same faculty can be scheduled to supervise on blocks where they already have an inpatient assignment.

Suggested approach: store preserved assignments and skip those faculty for those blocks.

```diff
diff --git a/backend/app/scheduling/engine.py b/backend/app/scheduling/engine.py
--- a/backend/app/scheduling/engine.py
+++ b/backend/app/scheduling/engine.py
@@
         if preserve_fmit:
             fmit_assignments = self._load_fmit_assignments()
             preserve_ids = {a.id for a in fmit_assignments}
             if fmit_assignments:
                 logger.info(
                     f"Preserving {len(fmit_assignments)} FMIT faculty assignments"
                 )
+        self._preserved_assignments = fmit_assignments
@@
     def _assign_faculty(self, faculty: list[Person], blocks: list[Block]):
@@
         # Assign faculty to each block
         faculty_assignments = {f.id: 0 for f in faculty}
+        preserved_pairs = {
+            (a.person_id, a.block_id)
+            for a in getattr(self, "_preserved_assignments", [])
+        }
@@
         available = [
             f for f in faculty
-            if self._is_available(f.id, block_id)
+            if self._is_available(f.id, block_id)
+            and (f.id, block_id) not in preserved_pairs
         ]
```

Alternative: mark preserved assignments in `availability_matrix` during `_build_availability_matrix` so the availability check blocks them.

## 3) Make admin credentials configurable in seed script

Problem: the seed script hardcodes the admin password (`admin123`), which is environment-specific and leaves credentials embedded in source.

Suggested approach: read username/password from environment variables with sensible defaults.

```diff
diff --git a/scripts/seed_people.py b/scripts/seed_people.py
--- a/scripts/seed_people.py
+++ b/scripts/seed_people.py
@@
-import requests
-import json
-import sys
+import os
+import requests
+import json
+import sys
@@
-# Login to get token
+admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
+admin_password = os.getenv("SEED_ADMIN_PASSWORD", "AdminPassword123!")
+
+# Login to get token
 login_resp = requests.post(
     f"{BASE_URL}/api/v1/auth/login/json",
-    json={"username": "admin", "password": "admin123"}
+    json={"username": admin_username, "password": admin_password}
 )
```

## 4) Airtable absence import: normalize names before matching

Problem: Airtable names won't match local names if titles like "Dr." are stored locally, causing many absences to be skipped.

Suggested approach: normalize both sides (strip titles/suffixes, collapse whitespace) before mapping.

```diff
diff --git a/scripts/airtable_sync.py b/scripts/airtable_sync.py
--- a/scripts/airtable_sync.py
+++ b/scripts/airtable_sync.py
@@
+def normalize_name(name: str) -> str:
+    """Normalize person names for matching."""
+    cleaned = (name or "").lower().strip()
+    for prefix in ("dr. ", "dr ", "md ", "mr ", "mrs ", "ms "):
+        if cleaned.startswith(prefix):
+            cleaned = cleaned[len(prefix):]
+    return " ".join(cleaned.split())
@@
     person_map = {}
     for person in resp.get("items", []):
         name = person.get("name", "")
         person_id = person.get("id", "")
         if name and person_id:
-            person_map[name.lower()] = person_id
+            person_map[normalize_name(name)] = person_id
@@
             name = f"{first_name} {last_name}"
-            airtable_map[airtable_id] = name.lower()
+            airtable_map[airtable_id] = normalize_name(name)
```

Note: `airtable_sync.py` is now gitignored (local-only script).
