# Template Versioning System

> **Version:** 1.0
> **Purpose:** Manage template evolution and compatibility

---

## Version Numbering: MAJOR.MINOR

### MAJOR Version Change
- Significant functionality change
- Breaking changes to template structure
- New required variables
- Changed process flow

**Example:** 1.0 → 2.0

### MINOR Version Change
- Bug fixes
- New optional variables
- Performance improvements
- Documentation updates

**Example:** 1.0 → 1.1

---

## Template Header Format

```markdown
# Agent Name - Prompt Templates

> **Role:** ${ROLE}
> **Model:** Claude Opus 4.5
> **Mission:** ${MISSION}
> **Version:** 1.0
> **Last Updated:** 2025-12-31
```

---

## Version History Tracking

Each template file should include:
```
## Version History
- v1.1 (2025-12-31): Bug fix in ACGME validation
- v1.0 (2025-12-15): Initial release
```

---

## Backward Compatibility

- MAJOR versions: No guarantee of compatibility
- MINOR versions: Always backward compatible
- Deprecated variables: Mark with `[DEPRECATED]`

---

## Upgrade Path

When upgrading templates:
1. Review breaking changes
2. Update variable mappings
3. Test with new version
4. Archive old version
5. Document migration

---

*Last Updated: 2025-12-31*
