# Gemini Prompt: Doc Archival Sweep

Execute the doc archival task defined in `docs/tasks/GEMINI_DOC_ARCHIVAL_TASK.md`.

This is a mechanical task: move 81 stale markdown files to `docs/archived/` using `git mv`. No content editing. Read the task doc for the exact file list, target directories, commit message, and PR template.

Steps:
1. Read `docs/tasks/GEMINI_DOC_ARCHIVAL_TASK.md` in full
2. Checkout a clean branch from `main`
3. Execute all `git mv` commands in Parts 1-4
4. Run the verification checks
5. Commit, push, and open PR

If any `git mv` fails because a file doesn't exist, skip it and note which files were missing. Do not abort the entire task for a single missing file.
