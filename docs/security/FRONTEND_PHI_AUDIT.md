# Frontend PHI Handling Audit

**Date:** 2026-01-04
**Auditor:** COORD_FRONTEND (Sonnet 4.5)
**Scope:** React/Next.js frontend codebase
**Purpose:** Identify Protected Health Information (PHI) exposure risks

---

## Executive Summary

**Overall Assessment:** LOW RISK with recommended improvements

The frontend demonstrates good PHI handling practices with most console.log statements commented out or containing only documentation examples. However, several areas require attention:

- **CRITICAL:** 3 findings (user-facing PHI in error messages)
- **HIGH:** 2 findings (console logging in error handlers)
- **MEDIUM:** 5 findings (PHI displayed without additional protection)
- **LOW:** Multiple commented-out console.logs (good practice)

---

## CRITICAL Findings

### C1. Person Names in User-Facing Error Messages

**Severity:** CRITICAL
**Files:**
- `/frontend/src/components/schedule/EditAssignmentModal.tsx:434`
- `/frontend/src/app/people/page.tsx:184`
- `/frontend/src/app/templates/page.tsx:118`

**Issue:**
Confirmation dialogs display person names in delete confirmations:

```tsx
// EditAssignmentModal.tsx:434
message={`Are you sure you want to delete this ${session} assignment for ${person?.name || 'this person'} on ${formattedDate}?`}

// people/page.tsx:184
message={`Are you sure you want to delete ${personToDelete?.name || 'this person'}?`}
```

**Risk:**
- Screen sharing during confirmation could expose resident/faculty names
- Browser screenshots/recordings capture PHI
- Error reporting tools may capture modal text

**Recommendation:**
Replace with anonymized references:
```tsx
message={`Are you sure you want to delete this assignment on ${formattedDate}?`}
// OR use role-based reference:
message={`Are you sure you want to delete this ${personType} assignment?`}
```

---

### C2. Person Names in ACGME Violation Warnings

**Severity:** CRITICAL
**Files:**
- `/frontend/src/components/schedule/AssignmentWarnings.tsx:192`
- `/frontend/src/components/schedule/AssignmentWarnings.tsx:215`
- `/frontend/src/components/schedule/AssignmentWarnings.tsx:232`

**Issue:**
Warning messages include person names:

```tsx
// Line 192
message: `This assignment would put ${context.personName || 'this person'} at ${hoursAfterAssignment} hours...`

// Line 215
message: `${context.personName || 'This person'} is already assigned to ${conflictingAssignment.rotationName}...`

// Line 232
message: `${context.personName || 'This person'} has a recorded ${conflictingAbsence.type.replace('_', ' ')} absence...`
```

**Risk:**
- Warning toasts may be visible during screen sharing
- Browser extensions may capture toast content
- Screenshot tools capture PHI

**Recommendation:**
Use contextual references:
```tsx
message: `This assignment would exceed the ${context.maxWeeklyHours}-hour weekly limit`
message: `Time conflict with existing assignment to ${conflictingAssignment.rotationName}`
message: `Absence recorded on this date`
```

---

### C3. Absence Types Exposed in User-Facing Messages

**Severity:** CRITICAL
**File:** `/frontend/src/components/schedule/AssignmentWarnings.tsx:232`

**Issue:**
Absence types (sick, medical, bereavement, etc.) are displayed:

```tsx
message: `${context.personName || 'This person'} has a recorded ${conflictingAbsence.type.replace('_', ' ')} absence on this date.`
```

**Risk:**
- Medical absence types are PHI (sick, medical, convalescent, maternity_paternity)
- Family emergency and bereavement reveal personal circumstances
- Violates PERSEC requirements for military medical data

**Recommendation:**
```tsx
message: `Absence recorded on this date. Please verify coverage.`
```

---

## HIGH Findings

### H1. Console Logging in Production Error Handler

**Severity:** HIGH
**Files:**
- `/frontend/src/components/ErrorBoundary.tsx:229-234`
- `/frontend/src/app/providers.tsx:18-28`

**Issue:**
Error boundary logs full error details including component stack:

```tsx
// ErrorBoundary.tsx:229-234
console.error('Error:', error);
console.error('Error Name:', error.name);
console.error('Error Message:', error.message);
console.error('Error Stack:', error.stack);
console.error('Component Stack:', errorInfo.componentStack);
```

**Risk:**
- Browser console may contain PHI if errors occur during person/absence rendering
- Developer tools recording captures console output
- Error monitoring tools may scrape console

**Current Mitigation:**
Most critical console.error calls in `/frontend/src/lib/errors/error-handler.ts` are commented out (lines 104-110).

**Recommendation:**
1. Wrap production console.error in environment check:
```tsx
if (process.env.NODE_ENV === 'development') {
  console.error('Error:', error);
}
```

2. Sanitize error messages before logging:
```tsx
const sanitizedMessage = error.message.replace(/\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, '[REDACTED]');
```

---

### H2. Person Email Addresses in Auth Logging

**Severity:** HIGH
**File:** `/frontend/src/lib/auth.ts:163-166, 262-266, 293-298, 344-347`

**Issue:**
Authentication examples show username logging (all commented out, but pattern is risky):

```tsx
// auth.ts:163-166 (commented examples)
*   console.log(`Logged in as: ${response.user.username}`);
*   console.log(`Role: ${response.user.role}`);
```

**Risk:**
- If uncommented during debugging, captures usernames (may be email addresses)
- Pattern may be copied elsewhere

**Current Mitigation:**
All instances are commented out (good!)

**Recommendation:**
Add warning comment:
```tsx
// WARNING: Never log user.username in production (may contain email/PHI)
// Use user.id or user.role for debugging
```

---

## MEDIUM Findings

### M1. Person Names Displayed in UI Components

**Severity:** MEDIUM
**Files:** 161 files found with person name rendering

**Issue:**
Components directly render person.name without additional protection:

```tsx
// AbsenceList.tsx:95
{person?.name || 'Unknown'}

// ScheduleCell.tsx, ScheduleGrid.tsx, etc.
{assignment.person.name}
```

**Risk:**
- Screen sharing exposes PHI
- Browser screenshots capture names
- No encryption at rest in browser cache

**Current Mitigation:**
- RBAC controls who can view schedules
- HTTPS protects data in transit
- httpOnly cookies prevent XSS

**Recommendation:**
1. Add data-sensitive attribute for screenshot tools:
```tsx
<span data-sensitive="phi">{person?.name}</span>
```

2. Consider blur-on-hover for demo mode:
```tsx
<span className={demoMode ? 'blur-sm hover:blur-none' : ''}>
  {person?.name}
</span>
```

---

### M2. Email Addresses in Contact Info Component

**Severity:** MEDIUM
**File:** `/frontend/src/features/call-roster/ContactInfo.tsx`

**Issue:**
Displays phone, pager, and email with click-to-copy:

```tsx
// Lines 37-44
const hasContact = person.phone || person.pager || person.email;
```

**Risk:**
- Email addresses are PII/PHI
- Copy-to-clipboard may log to analytics
- Browser extensions may scrape contact info

**Current Mitigation:**
- Failed copy attempts don't log error (line 33 commented out)
- Component only renders for authorized users

**Recommendation:**
Add clipboard permission check and sanitize analytics:
```tsx
const handleCopy = async (text: string, field: string) => {
  try {
    await navigator.clipboard.writeText(text);
    setCopiedField(field); // Don't send field value to analytics
  } catch (err) {
    // Don't log error - may contain PHI
  }
};
```

---

### M3. Absence Types Visible in AbsenceList Component

**Severity:** MEDIUM
**File:** `/frontend/src/components/AbsenceList.tsx:16-33, 89`

**Issue:**
Absence types color-coded and displayed in table:

```tsx
// Lines 20-22
sick: 'bg-red-100 text-red-800',
medical: 'bg-red-100 text-red-800',
convalescent: 'bg-red-200 text-red-900',
maternity_paternity: 'bg-pink-100 text-pink-800',
```

**Risk:**
- Medical absence types reveal health conditions (PHI)
- Color coding makes absence type visible from distance
- Table column displays absence type prominently

**Current Mitigation:**
- Only authorized coordinators/admins can view absence page
- RBAC enforced at API and route level

**Recommendation:**
Add option to display generic "Medical Leave" instead of specific type for non-admins:
```tsx
const displayType = userRole === 'admin'
  ? absence.absence_type
  : absence.absence_type.match(/sick|medical|convalescent/)
    ? 'medical_leave'
    : absence.absence_type;
```

---

### M4. Person Names in Schedule Cell Tooltips

**Severity:** MEDIUM
**File:** Multiple schedule components (ScheduleCell.tsx, ScheduleGrid.tsx, etc.)

**Issue:**
Hover tooltips likely display person names (inferred from usage patterns)

**Risk:**
- Tooltips visible during screen recording
- May be captured by accessibility tools
- DOM inspection reveals PHI

**Recommendation:**
Audit tooltip content and sanitize if needed:
```tsx
title={demoMode ? `Resident ${index + 1}` : person.name}
```

---

### M5. Search/Filter Results May Expose PHI

**Severity:** MEDIUM
**Files:**
- `/frontend/src/components/schedule/PersonFilter.tsx`
- `/frontend/src/features/templates/components/TemplateSearch.tsx`

**Issue:**
Search results display person names in dropdown/autocomplete

**Risk:**
- Browser autocomplete history stores PHI
- Search suggestions visible over shoulder
- DOM inspection reveals recently searched names

**Current Mitigation:**
- autocomplete="off" may be set (not verified)

**Recommendation:**
Verify and enforce:
```tsx
<input
  autoComplete="off"
  data-lpignore="true"  // Disable LastPass
  data-form-type="other"  // Disable browser autofill
/>
```

---

## LOW Findings

### L1. Commented Console.log Statements

**Severity:** LOW (Good Practice!)
**Status:** No action needed

**Findings:**
The codebase demonstrates excellent discipline with 50+ console.log statements properly commented out:

```tsx
// Properly commented examples:
// console.error('Failed to copy:', err);  // ContactInfo.tsx:33
// console.error('Failed to accept swap');  // SwapRequestCard.tsx:135
// console.log('Handle swap action for:', _swapId);  // MyLifeDashboard.tsx:68
```

**Recommendation:**
Continue this practice. Consider ESLint rule to block uncommented console.log:
```json
{
  "rules": {
    "no-console": ["error", { "allow": ["warn", "error"] }]
  }
}
```

---

### L2. Documentation Examples Contain PHI References

**Severity:** LOW
**Files:**
- `/frontend/src/lib/api.ts:260`
- `/frontend/src/lib/auth.ts:163-347`
- Various validation.ts examples

**Issue:**
JSDoc examples reference person.name, user.username, etc.

**Risk:**
Minimal - documentation only, never executed

**Recommendation:**
Use clearly fake examples:
```tsx
// Good: console.log(user.name); // "Alice Smith"
// Better: console.log(user.name); // "Demo User 123"
```

---

## Summary by Component Type

| Component Type | PHI Exposed | Severity | Recommendation |
|---------------|-------------|----------|----------------|
| Error Messages | Person names, absence types | CRITICAL | Anonymize messages |
| Console Logging | Full error details | HIGH | Conditional logging |
| UI Display | Names, emails, phones | MEDIUM | Add data-sensitive tags |
| Tooltips/Search | Names in autocomplete | MEDIUM | Disable autocomplete |
| Documentation | Example PHI | LOW | Use fake data |

---

## Remediation Priority

### Immediate (This Sprint)
1. **Remove person names from error messages** (C1, C2)
2. **Anonymize absence types in warnings** (C3)
3. **Add environment check to console.error** (H1)

### Short-term (Next Sprint)
4. Add data-sensitive attributes to PHI elements (M1)
5. Audit tooltip content (M4)
6. Add autocomplete protections to search (M5)

### Long-term (Backlog)
7. Implement demo mode with PHI blurring (M1)
8. Add ESLint rule for console.log (L1)
9. Review third-party libraries for PHI logging

---

## Compliance Notes

### HIPAA Considerations
- **Minimum Necessary:** UI displays more PHI than needed (person names in delete confirmations)
- **Audit Trail:** No evidence of PHI access logging in frontend (likely handled by backend)
- **Encryption:** HTTPS enforced, httpOnly cookies used

### Military PERSEC/OPSEC
- **Good:** No deployment/TDY data in frontend logs
- **Risk:** Absence types reveal personal circumstances
- **Recommendation:** Further anonymize military-specific absence types

---

## Testing Recommendations

1. **Automated PHI Detection:**
   ```bash
   # Add to CI/CD
   grep -r "person\.name\|person\.email" frontend/src --include="*.tsx" | grep -v "test\|comment"
   ```

2. **Manual Testing:**
   - Screen share during demo and verify no PHI visible in errors
   - Check browser console during error scenarios
   - Test with browser DevTools Network/Console tabs open

3. **Security Review:**
   - Penetration test: inject errors to see what gets logged
   - Review Sentry/error reporting tool configuration
   - Verify analytics doesn't capture form field values

---

## References

- CLAUDE.md Security Requirements (Lines 145-190)
- HIPAA Minimum Necessary Rule
- Military PERSEC Guidelines
- Frontend Error Handler: `/frontend/src/lib/errors/error-handler.ts`

---

**Next Steps:**
1. Create tickets for CRITICAL findings (C1-C3)
2. Schedule security review with team
3. Update ESLint configuration
4. Add PHI handling to onboarding documentation

**Auditor Note:**
This audit was performed by automated code analysis. Manual testing recommended to verify runtime behavior, especially error handling paths and third-party integrations.
