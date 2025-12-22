# Review Patches for Claude (Latest Changes)

This document proposes concrete fixes for issues found in the latest code changes.

## 1) Daily Manifest "ALL" filter should omit `time_of_day`

Problem: the API only accepts `AM` or `PM` when `time_of_day` is present. The UI sends `ALL`, which triggers a 400.

Suggested approach: build the query string so that `time_of_day` is only included for `AM` or `PM`.

```diff
diff --git a/frontend/src/features/daily-manifest/hooks.ts b/frontend/src/features/daily-manifest/hooks.ts
index 9d8f0b6..XXXXXXX 100644
--- a/frontend/src/features/daily-manifest/hooks.ts
+++ b/frontend/src/features/daily-manifest/hooks.ts
@@
 export function useDailyManifest(
   date: string,
   timeOfDay: 'AM' | 'PM' | 'ALL' = 'AM',
   options?: Omit<UseQueryOptions<DailyManifestData, ApiError>, 'queryKey' | 'queryFn'>
 ) {
+  const params = new URLSearchParams({ date });
+  if (timeOfDay !== 'ALL') {
+    params.set('time_of_day', timeOfDay);
+  }
   return useQuery<DailyManifestData, ApiError>({
     queryKey: manifestQueryKeys.byDate(date, timeOfDay),
     queryFn: () =>
       get<DailyManifestData>(
-        `/daily-manifest?date=${date}&time_of_day=${timeOfDay}`
+        `/daily-manifest?${params.toString()}`
       ),
@@
   });
 }
```

Optional: update the query key to avoid caching issues between `ALL` and null if needed.

