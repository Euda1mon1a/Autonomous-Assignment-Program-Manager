# Template Validation Rules

> **Version:** 1.0
> **Purpose:** Ensure template quality and consistency

---

## Pre-Execution Validation

### 1. Variable Completeness Check
- [ ] No `${VARIABLE}` placeholders remain
- [ ] All required variables initialized
- [ ] Variable types match specifications
- [ ] Sensitive data sanitized

### 2. Process Flow Check
- [ ] All steps sequential and logical
- [ ] No missing prerequisites
- [ ] Exit conditions defined
- [ ] Error handling present

### 3. Output Format Check
- [ ] Output format specified
- [ ] Example provided
- [ ] All required fields present
- [ ] Data types correct

---

## ACGME Compliance Validation

For all scheduling-related templates:

- [ ] 80-hour rule enforcement present
- [ ] 1-in-7 rule enforcement present
- [ ] Supervision ratio validation present
- [ ] Credential verification included
- [ ] Compliance verdict reported

---

## Quality Gates

### Fail Criteria (Block Execution)
- Required variable missing
- ACGME violation possible
- Security vulnerability detected
- Data integrity issue found

### Warn Criteria (Allow with Caution)
- Sub-optimal performance expected
- Coverage < target threshold
- Workload imbalance detected
- Preference conflict identified

### Pass Criteria (Safe to Execute)
- All variables initialized
- Process flow sound
- Compliance verified
- Quality gates passed

---

## Continuous Validation

During execution:
- Monitor for timeouts
- Check for infinite loops
- Validate intermediate results
- Verify resource consumption

---

*Last Updated: 2025-12-31*
