---
name: changelog-generator
description: Automatically generate user-friendly changelogs from git commit history. Use when preparing release notes, documenting changes for stakeholders, or creating app store descriptions.
---

# Changelog Generator Skill

Transforms technical git commits into polished, user-friendly changelogs that stakeholders can understand.

## When This Skill Activates

- Preparing release notes for deployment
- Creating weekly/monthly change summaries
- Documenting updates for non-technical stakeholders
- Generating app store update descriptions
- Summarizing PR changes for review

## Core Workflow

1. Scan git history for specified time range or version
2. Categorize commits by type (features, fixes, etc.)
3. Filter out internal commits (refactors, tests, chores)
4. Transform developer language into user-friendly descriptions
5. Format as structured changelog

## Commit Categories

| Category | Prefixes | User-Friendly Label |
|----------|----------|---------------------|
| Features | `feat:`, `feature:`, `add:` | New Features |
| Fixes | `fix:`, `bugfix:`, `hotfix:` | Bug Fixes |
| Improvements | `improve:`, `enhance:`, `update:` | Improvements |
| Breaking | `BREAKING:`, `breaking:` | Breaking Changes |
| Security | `security:`, `sec:` | Security Updates |
| Performance | `perf:`, `performance:` | Performance |

### Filtered Out (Internal)

- `refactor:`, `refactoring:`
- `test:`, `tests:`
- `chore:`, `build:`
- `ci:`, `cd:`
- `docs:` (unless user-facing)
- `style:`, `lint:`
- Merge commits

## Usage Examples

### Generate Changelog for Date Range

```bash
# In repository root
git log --oneline --since="2025-01-01" --until="2025-01-31"
```

Prompt:
```
Generate a changelog for commits between January 1-31, 2025.
Focus on user-facing changes. Group by category.
```

### Generate Changelog for Version

```bash
# Between tags
git log --oneline v1.2.0..v1.3.0
```

Prompt:
```
Generate release notes for version 1.3.0.
Include all changes since v1.2.0.
```

### Generate Weekly Summary

```bash
git log --oneline --since="1 week ago"
```

Prompt:
```
Create a weekly update summary for stakeholders.
Highlight the most impactful changes.
```

## Output Format

### Standard Changelog

```markdown
# Changelog - Version X.Y.Z

**Release Date:** YYYY-MM-DD

## New Features

- **Schedule Swap Automation**: Faculty can now request schedule swaps that are automatically matched with compatible candidates
- **Coverage Matrix View**: New visualization showing rotation coverage across all dates

## Improvements

- Enhanced ACGME compliance dashboard with real-time violation alerts
- Improved schedule export performance for large date ranges

## Bug Fixes

- Fixed issue where overnight shifts were incorrectly split across two days
- Resolved timezone display bug in schedule calendar view

## Security Updates

- Updated authentication token expiration handling

---

*For technical details, see the [commit history](link)*
```

### Compact Format (App Store Style)

```markdown
What's New in Version X.Y.Z:

• Automatic schedule swap matching - request swaps and find compatible partners instantly
• Real-time ACGME compliance alerts
• Faster schedule exports
• Bug fixes and performance improvements
```

## Transformation Rules

### Developer → User Language

| Developer Term | User-Friendly Term |
|----------------|-------------------|
| "Implement X endpoint" | "Added X feature" |
| "Fix N+1 query in X" | "Improved X loading speed" |
| "Add validation for X" | "Enhanced X reliability" |
| "Refactor X service" | (filter out) |
| "Update dependencies" | (filter out unless security) |
| "Add tests for X" | (filter out) |

### Example Transformations

```
# Original commit messages
feat: implement swap auto-matcher algorithm
fix: resolve race condition in assignment creation
perf: optimize schedule query with eager loading
refactor: extract validation logic to separate service
test: add unit tests for swap executor
chore: update pytest to 8.0

# Transformed changelog
## New Features
- **Swap Auto-Matching**: System now automatically finds compatible swap partners

## Bug Fixes
- Fixed issue where simultaneous schedule changes could cause conflicts

## Performance
- Schedule loading is now 3x faster

# (refactor, test, chore filtered out)
```

## Integration with Project

### Slash Command

Create `/project:changelog` command:

```markdown
# .claude/commands/changelog.md

Generate a changelog for the specified time range.

Usage: /project:changelog [since] [until]

Examples:
- /project:changelog "1 week ago"
- /project:changelog "v1.2.0" "v1.3.0"
- /project:changelog "2025-01-01" "2025-01-31"

Steps:
1. Run: git log --oneline --since="$1" ${2:+--until="$2"}
2. Categorize commits by conventional commit prefix
3. Filter internal commits (refactor, test, chore, ci)
4. Transform to user-friendly language
5. Output in standard changelog format
```

### Automated Release Notes

```python
# scripts/generate_changelog.py
import subprocess
from datetime import datetime

def generate_changelog(since: str, until: str = None) -> str:
    """Generate changelog from git history."""
    cmd = ['git', 'log', '--oneline', f'--since={since}']
    if until:
        cmd.append(f'--until={until}')

    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = result.stdout.strip().split('\n')

    # Categorize
    categories = {
        'features': [],
        'fixes': [],
        'improvements': [],
        'breaking': [],
        'security': [],
        'performance': [],
    }

    for commit in commits:
        if not commit:
            continue

        hash_id, message = commit.split(' ', 1)

        # Categorize based on prefix
        if message.startswith(('feat:', 'feature:', 'add:')):
            categories['features'].append(message)
        elif message.startswith(('fix:', 'bugfix:', 'hotfix:')):
            categories['fixes'].append(message)
        elif message.startswith(('improve:', 'enhance:', 'update:')):
            categories['improvements'].append(message)
        elif message.startswith(('BREAKING:', 'breaking:')):
            categories['breaking'].append(message)
        elif message.startswith(('security:', 'sec:')):
            categories['security'].append(message)
        elif message.startswith(('perf:', 'performance:')):
            categories['performance'].append(message)
        # Skip: refactor, test, chore, ci, docs, style, lint, merge

    return format_changelog(categories)


def format_changelog(categories: dict) -> str:
    """Format categorized commits as markdown."""
    sections = []

    if categories['breaking']:
        sections.append("## Breaking Changes\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['breaking']))

    if categories['features']:
        sections.append("## New Features\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['features']))

    if categories['improvements']:
        sections.append("## Improvements\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['improvements']))

    if categories['fixes']:
        sections.append("## Bug Fixes\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['fixes']))

    if categories['security']:
        sections.append("## Security Updates\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['security']))

    if categories['performance']:
        sections.append("## Performance\n" +
            "\n".join(f"- {clean_message(m)}" for m in categories['performance']))

    return "\n\n".join(sections)


def clean_message(message: str) -> str:
    """Remove prefix and clean up commit message."""
    # Remove conventional commit prefix
    if ':' in message:
        message = message.split(':', 1)[1].strip()

    # Capitalize first letter
    return message[0].upper() + message[1:] if message else message
```

## Best Practices

### Writing Changelog-Friendly Commits

```bash
# Good - clear, user-facing language
git commit -m "feat: add schedule export to PDF format"
git commit -m "fix: resolve double-booking issue for overnight shifts"

# Bad - too technical
git commit -m "feat: implement PDFExporter class with reportlab"
git commit -m "fix: add with_for_update() to prevent race condition"
```

### Grouping Related Changes

When multiple commits relate to one feature:
```markdown
## New Features

- **Schedule Export Overhaul**: Export schedules to PDF and Excel formats with improved formatting and compliance summaries
  - PDF exports now include ACGME compliance status
  - Excel exports preserve formulas for further analysis
  - Both formats support custom date ranges
```

### Highlighting Impact

Emphasize changes that matter to users:
```markdown
## Performance

- **3x Faster Schedule Loading**: Optimized database queries for schedule retrieval
- Schedule generation now completes in under 5 seconds for full academic year
```

## Verification Checklist

Before publishing changelog:

- [ ] All user-facing changes are included
- [ ] Technical jargon is translated to plain language
- [ ] Breaking changes are clearly highlighted
- [ ] Security updates are noted (without exposing vulnerabilities)
- [ ] Internal changes (refactor, test, chore) are filtered out
- [ ] Format is consistent and readable

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- Project changelog: `CHANGELOG.md`
