# Review Patches for Claude (New Findings)

This document proposes concrete fixes for the newest review findings.

## 1) Conflict list filters: validate enums + bad UUIDs

Problem: filters accept raw strings and parse UUIDs without error handling, which can raise 500s or return empty results.

Suggested approach:
- Normalize filter tokens to enums.
- Catch invalid values and return HTTP 400 with a clear message.

```diff
diff --git a/backend/app/api/routes/conflict_resolution.py b/backend/app/api/routes/conflict_resolution.py
index 5bbffa6..XXXXXXX 100644
--- a/backend/app/api/routes/conflict_resolution.py
+++ b/backend/app/api/routes/conflict_resolution.py
@@
 from app.core.security import get_current_active_user
@@
-from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity, ConflictType
+from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity, ConflictType
@@
 def list_conflicts(
@@
 ):
@@
     # Apply filters
     if types:
-        type_list = [t.strip() for t in types.split(",")]
-        query = query.filter(ConflictAlert.conflict_type.in_(type_list))
+        try:
+            type_list = [ConflictType(t.strip()) for t in types.split(",")]
+        except ValueError:
+            raise HTTPException(
+                status_code=status.HTTP_400_BAD_REQUEST,
+                detail="Invalid conflict type value",
+            )
+        query = query.filter(ConflictAlert.conflict_type.in_(type_list))
@@
     if severities:
-        severity_list = [s.strip() for s in severities.split(",")]
-        query = query.filter(ConflictAlert.severity.in_(severity_list))
+        try:
+            severity_list = [ConflictSeverity(s.strip()) for s in severities.split(",")]
+        except ValueError:
+            raise HTTPException(
+                status_code=status.HTTP_400_BAD_REQUEST,
+                detail="Invalid severity value",
+            )
+        query = query.filter(ConflictAlert.severity.in_(severity_list))
@@
     if statuses:
-        status_list = [s.strip() for s in statuses.split(",")]
-        query = query.filter(ConflictAlert.status.in_(status_list))
+        try:
+            status_list = [ConflictAlertStatus(s.strip()) for s in statuses.split(",")]
+        except ValueError:
+            raise HTTPException(
+                status_code=status.HTTP_400_BAD_REQUEST,
+                detail="Invalid status value",
+            )
+        query = query.filter(ConflictAlert.status.in_(status_list))
@@
     if person_ids:
-        person_id_list = [UUID(p.strip()) for p in person_ids.split(",")]
+        try:
+            person_id_list = [UUID(p.strip()) for p in person_ids.split(",")]
+        except ValueError:
+            raise HTTPException(
+                status_code=status.HTTP_400_BAD_REQUEST,
+                detail="Invalid person_ids UUID value",
+            )
         query = query.filter(ConflictAlert.faculty_id.in_(person_id_list))
```

## 2) Conflict list sorting: restrict sort fields

Problem: `sort_by` is passed into `getattr`, which can sort by unexpected attributes or relationships.

Suggested approach: whitelist sortable columns.

```diff
diff --git a/backend/app/api/routes/conflict_resolution.py b/backend/app/api/routes/conflict_resolution.py
index 5bbffa6..XXXXXXX 100644
--- a/backend/app/api/routes/conflict_resolution.py
+++ b/backend/app/api/routes/conflict_resolution.py
@@
     # Apply sorting
-    sort_column = getattr(ConflictAlert, sort_by, ConflictAlert.created_at)
+    sortable_fields = {
+        "created_at": ConflictAlert.created_at,
+        "fmit_week": ConflictAlert.fmit_week,
+        "severity": ConflictAlert.severity,
+        "status": ConflictAlert.status,
+    }
+    sort_column = sortable_fields.get(sort_by, ConflictAlert.created_at)
```

## 3) Import preview: callback dependencies include `dataTypeSource`

Problem: `previewImport` depends on `dataTypeSource` but the hook’s dependency list doesn’t include it, so it can close over stale values.

Suggested approach: include `state.dataTypeSource` in the dependency array.

```diff
diff --git a/frontend/src/features/import-export/useImport.ts b/frontend/src/features/import-export/useImport.ts
index 6730792..XXXXXXX 100644
--- a/frontend/src/features/import-export/useImport.ts
+++ b/frontend/src/features/import-export/useImport.ts
@@
-  }, [state.dataType, parseFile, updateProgress]);
+  }, [state.dataType, state.dataTypeSource, parseFile, updateProgress]);
```

## 4) Daily manifest docstring example: update to new canonical path

Problem: docstring example still references legacy path.

Suggested approach: update the example to `/api/daily-manifest`.

```diff
diff --git a/backend/app/api/routes/daily_manifest.py b/backend/app/api/routes/daily_manifest.py
index 0f71807..XXXXXXX 100644
--- a/backend/app/api/routes/daily_manifest.py
+++ b/backend/app/api/routes/daily_manifest.py
@@
-    Example: GET /api/assignments/daily-manifest?date=2025-01-15&time_of_day=AM
+    Example: GET /api/daily-manifest?date=2025-01-15&time_of_day=AM
```
