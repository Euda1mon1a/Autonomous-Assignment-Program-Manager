# Review Patches for Claude

This document proposes concrete patches for issues found in the review. Apply selectively.

## 1) Daily Manifest: keep legacy `/assignments/daily-manifest` path

Problem: the API moved to `/daily-manifest` only, which breaks clients that still call `/assignments/daily-manifest`.

Suggested approach: add a legacy router with an explicit `/daily-manifest` path, and mount it at `/assignments` with `include_in_schema=False`.

```diff
diff --git a/backend/app/api/routes/daily_manifest.py b/backend/app/api/routes/daily_manifest.py
index 011448d..XXXXXXX 100644
--- a/backend/app/api/routes/daily_manifest.py
+++ b/backend/app/api/routes/daily_manifest.py
@@
-router = APIRouter()
+router = APIRouter()
+legacy_router = APIRouter()
@@
-@router.get("", response_model=DailyManifestResponse)
+@router.get("", response_model=DailyManifestResponse)
 def get_daily_manifest(
@@
-    Example: GET /api/assignments/daily-manifest?date=2025-01-15&time_of_day=AM
+    Example: GET /api/daily-manifest?date=2025-01-15&time_of_day=AM
     """
@@
     return DailyManifestResponse(
         date=date_param,
         locations=locations,
         summary=StaffingSummary(
             total=total,
             residents=residents,
             faculty=faculty,
             locations=len(locations),
         ),
     )
+
+
+@legacy_router.get("/daily-manifest", response_model=DailyManifestResponse, include_in_schema=False)
+def get_daily_manifest_legacy(
+    date_param: date = Query(..., alias="date", description="Date for the manifest"),
+    time_of_day: str | None = Query(None, description="AM or PM (optional, shows all if omitted)"),
+    db: Session = Depends(get_db),
+    current_user: User = Depends(get_current_active_user),
+):
+    """Legacy endpoint kept for backward compatibility."""
+    return get_daily_manifest(date_param, time_of_day, db, current_user)
```

```diff
diff --git a/backend/app/api/routes/__init__.py b/backend/app/api/routes/__init__.py
index d7b54e6..XXXXXXX 100644
--- a/backend/app/api/routes/__init__.py
+++ b/backend/app/api/routes/__init__.py
@@
-api_router.include_router(daily_manifest.router, prefix="/daily-manifest", tags=["daily-manifest"])
+api_router.include_router(daily_manifest.router, prefix="/daily-manifest", tags=["daily-manifest"])
+api_router.include_router(daily_manifest.legacy_router, prefix="/assignments", tags=["daily-manifest"])
```

## 2) Import preview: honor manual type selection, otherwise auto-detect

Problem: preview always uses `state.dataType`, so if the user didn’t select a type the import will validate against the default.

Suggested approach: track whether the user explicitly set the type, and only auto-detect when still “auto”.

```diff
diff --git a/frontend/src/features/import-export/useImport.ts b/frontend/src/features/import-export/useImport.ts
index dc4f797..XXXXXXX 100644
--- a/frontend/src/features/import-export/useImport.ts
+++ b/frontend/src/features/import-export/useImport.ts
@@
 interface ImportState {
   file: File | null;
   format: ImportFileFormat;
   dataType: ImportDataType;
+  dataTypeSource: 'auto' | 'manual';
   preview: ImportPreviewResult | null;
   progress: ImportProgress;
   options: ImportOptions;
 }
@@
   const [state, setState] = useState<ImportState>({
     file: null,
     format: 'csv',
     dataType: hookOptions.dataType || 'schedules',
+    dataTypeSource: hookOptions.dataType ? 'manual' : 'auto',
     preview: null,
@@
-      // Use user's selection from state.dataType, or auto-detect from columns
-      // Note: state.dataType reflects user's dropdown selection via setDataType()
-      const detectedType = state.dataType;
+      const detectedType =
+        state.dataTypeSource === 'manual' ? state.dataType : detectDataType(columns);
@@
   const setDataType = useCallback((dataType: ImportDataType) => {
-    setState(prev => ({ ...prev, dataType }));
+    setState(prev => ({ ...prev, dataType, dataTypeSource: 'manual' }));
   }, []);
```

## 3) Pydantic schema: avoid mutable defaults

Problem: `errors` and `importedIds` use mutable list defaults.

Suggested approach: use `Field(default_factory=list)`.

```diff
diff --git a/backend/app/schemas/person.py b/backend/app/schemas/person.py
index 6a868d5..XXXXXXX 100644
--- a/backend/app/schemas/person.py
+++ b/backend/app/schemas/person.py
@@
-from pydantic import BaseModel, EmailStr, field_validator
+from pydantic import BaseModel, EmailStr, Field, field_validator
@@
 class BulkImportResult(BaseModel):
@@
-    errors: list[dict] = []
-    importedIds: list[str] = []
+    errors: list[dict] = Field(default_factory=list)
+    importedIds: list[str] = Field(default_factory=list)
```
