<!--
Generate user-friendly changelogs from git commit history.
Use when preparing release notes or documenting changes.
-->

Invoke the changelog-generator skill to create a changelog.

## Arguments

- `$ARGUMENTS` - Version range or "since last release" (e.g., "v1.0.0..v1.1.0" or "last 10 commits")

## Output

Generates changelog in format:
- Features added
- Bugs fixed
- Breaking changes
- Dependencies updated

Saves to CHANGELOG.md or specified file.
