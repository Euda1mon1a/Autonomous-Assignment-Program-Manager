# Test Scenarios Catalog

## Overview

This document catalogs all integration test scenarios for the Residency Scheduler application. Each scenario represents a real-world use case or workflow that must be tested to ensure system reliability.

## Test Categories

### 📅 Schedule Management

#### 1. Create Schedule Workflow
**File:** `tests/integration/api/test_schedule_workflow.py::test_create_schedule_workflow`

**Scenario:**
- Program coordinator creates a new schedule for upcoming rotation block
- Selects residents, faculty, and rotation templates
- System generates compliant schedule

**Steps:**
1. Create rotation templates
2. Create blocks for date range
3. Create assignments for residents
4. Validate ACGME compliance
5. Verify schedule created successfully

**Expected Outcome:**
- Schedule created without errors
- All assignments are valid
- ACGME rules are satisfied

---

#### 2. Modify Existing Schedule
**File:** `tests/integration/api/test_schedule_workflow.py::test_modify_schedule_workflow`

**Scenario:**
- Coordinator needs to reassign a resident to different rotation
- Updates existing assignment
- System validates change maintains compliance

**Steps:**
1. Retrieve existing assignment
2. Update assignment with new rotation
3. Verify change persisted
4. Check compliance still maintained

**Expected Outcome:**
- Assignment updated successfully
- No compliance violations introduced

---

#### 3. Bulk Schedule Generation
**File:** `tests/integration/api/test_schedule_workflow.py::test_bulk_schedule_generation_workflow`

**Scenario:**
- Generate schedule for 4-week rotation block
- Multiple residents and rotation types
- Optimize for coverage and fairness

**Steps:**
1. Create rotation templates
2. Create blocks for 4 weeks
3. Request bulk schedule generation
4. Verify assignments created

**Expected Outcome:**
- Schedule generated for all dates
- Workload distributed fairly
- Compliance maintained

---

### 🔄 Swap Management

#### 4. One-to-One Swap Request
**File:** `tests/integration/api/test_swap_workflow.py::test_one_to_one_swap_workflow`

**Scenario:**
- Two faculty members want to exchange shifts
- Request swap, get approval, execute swap
- System maintains audit trail

**Steps:**
1. Create assignments for both faculty
2. Create swap request
3. Approve swap (if required)
4. Execute swap
5. Verify assignments swapped

**Expected Outcome:**
- Swap completed successfully
- Assignments reflect swapped schedules
- Audit trail created

---

#### 5. Absorb Swap (Give Away Shift)
**File:** `tests/integration/api/test_swap_workflow.py::test_absorb_swap_workflow`

**Scenario:**
- Faculty member needs to give away a shift
- System finds potential takers
- Shift reassigned to volunteer

**Steps:**
1. Create assignment to give away
2. Create absorb swap request
3. Find potential takers
4. Execute swap with volunteer

**Expected Outcome:**
- Shift successfully reassigned
- Original assignee removed
- New assignee added

---

#### 6. Swap Auto-Matching
**File:** `tests/integration/api/test_swap_workflow.py::test_swap_auto_matching_workflow`

**Scenario:**
- Resident requests swap
- System automatically finds compatible matches
- Presents ranked options

**Steps:**
1. Create multiple assignments
2. Create swap request
3. Request auto-matching
4. Verify matches returned

**Expected Outcome:**
- Compatible swaps identified
- Matches ranked by quality
- All matches maintain compliance

---

### ✅ ACGME Compliance

#### 7. 80-Hour Rule Validation
**File:** `tests/integration/api/test_compliance_workflow.py::test_80_hour_rule_validation_workflow`

**Scenario:**
- Resident assigned to many shifts in one week
- System detects potential 80-hour violation
- Prevents or warns about non-compliant schedule

**Steps:**
1. Create week of blocks
2. Assign resident to most blocks
3. Check compliance
4. Verify violation detected

**Expected Outcome:**
- 80-hour violation flagged
- Warning or error returned
- Schedule not saved if non-compliant

---

#### 8. 1-in-7 Day Off Rule
**File:** `tests/integration/api/test_compliance_workflow.py::test_1_in_7_rule_validation_workflow`

**Scenario:**
- Resident scheduled for 7+ consecutive days
- System enforces mandatory day off
- Rejects schedule violating 1-in-7 rule

**Steps:**
1. Create 14 days of assignments
2. Assign resident to all days
3. Validate compliance
4. Verify violation detected

**Expected Outcome:**
- 1-in-7 violation flagged
- System prevents non-compliant schedule
- Suggests corrections

---

#### 9. Supervision Ratio Enforcement
**File:** `tests/integration/api/test_compliance_workflow.py::test_supervision_ratio_workflow`

**Scenario:**
- Procedure clinic requires supervision
- Too many residents assigned without adequate faculty
- System enforces supervision ratios

**Steps:**
1. Create supervised rotation template
2. Assign residents without faculty
3. Check supervision compliance
4. Add faculty to meet ratio

**Expected Outcome:**
- Supervision violation detected
- System requires faculty assignment
- Compliance achieved after faculty added

---

### 🚨 Emergency Coverage

#### 10. Sudden Absence Coverage
**File:** `tests/integration/scenarios/test_emergency_coverage.py::test_sudden_absence_coverage_scenario`

**Scenario:**
- Resident calls in sick
- System must find immediate replacement
- Coverage maintained without compromising compliance

**Steps:**
1. Create scheduled assignments
2. Report sudden absence
3. Request emergency coverage
4. Verify replacement found

**Expected Outcome:**
- Coverage identified quickly
- Replacement maintains compliance
- Notification sent to replacement

---

#### 11. Military Deployment Coverage
**File:** `tests/integration/scenarios/test_emergency_coverage.py::test_deployment_coverage_scenario`

**Scenario:**
- Faculty deployed on TDY
- Extended absence (30 days)
- System redistributes assignments

**Steps:**
1. Create assignments for faculty
2. Report deployment
3. Find long-term replacement
4. Redistribute workload

**Expected Outcome:**
- Deployment coverage arranged
- Workload distributed fairly
- No single person overloaded

---

#### 12. N-1 Contingency Test
**File:** `tests/integration/scenarios/test_emergency_coverage.py::test_n_minus_2_failure_scenario`

**Scenario:**
- System tests resilience against single failure
- Simulates one resident unavailable
- Verifies coverage can be maintained

**Steps:**
1. Create minimal coverage schedule
2. Remove one resident
3. Test N-1 contingency
4. Verify coverage still possible

**Expected Outcome:**
- System can handle N-1 failure
- Coverage maintained
- Resilience confirmed

---

### 🔁 Cascade Failures

#### 13. Absence Triggers Overload
**File:** `tests/integration/scenarios/test_cascade_failures.py::test_absence_triggers_overload_scenario`

**Scenario:**
- Resident absence causes workload redistribution
- Redistribution may violate 80-hour rule for others
- System detects and prevents cascade

**Steps:**
1. Create balanced schedule
2. Remove one resident (absence)
3. Attempt redistribution
4. Check for compliance violations

**Expected Outcome:**
- Cascade risk detected
- System prevents overload
- Alternative solution found or escalated

---

### 🔒 Concurrent Modifications

#### 14. Concurrent Swap Requests
**File:** `tests/integration/scenarios/test_concurrent_modifications.py::test_concurrent_swap_requests_scenario`

**Scenario:**
- Two users request same swap simultaneously
- Race condition on swap acceptance
- System handles correctly

**Steps:**
1. Create swap scenario
2. Submit concurrent requests
3. Verify only one succeeds
4. Other gets conflict error

**Expected Outcome:**
- No data corruption
- Exactly one swap succeeds
- Clear error message for conflict

---

### 👥 Multi-User Scenarios

#### 15. Coordinator Approves Faculty Swap
**File:** `tests/integration/scenarios/test_multi_user.py::test_coordinator_approves_faculty_swap_scenario`

**Scenario:**
- Faculty requests swap
- Coordinator reviews and approves
- Workflow completed with proper authorization

**Steps:**
1. Faculty creates swap request
2. Coordinator receives notification
3. Coordinator approves request
4. Swap executed

**Expected Outcome:**
- Proper authorization enforced
- Workflow completes successfully
- Audit trail maintained

---

### 📊 Reporting

#### 16. Generate Compliance Report
**File:** `tests/integration/api/test_reporting_workflow.py::test_generate_compliance_report_workflow`

**Scenario:**
- Administrator generates monthly compliance report
- Report shows all ACGME metrics
- Export as PDF for record-keeping

**Steps:**
1. Request compliance report
2. Specify date range
3. Generate report
4. Export as PDF

**Expected Outcome:**
- Report generated successfully
- All metrics included
- PDF downloadable

---

### 📥 Import/Export

#### 17. CSV Schedule Import
**File:** `tests/integration/api/test_export_import.py::test_import_schedule_csv_workflow`

**Scenario:**
- Import schedule from CSV file
- Validate data before import
- Create assignments from import

**Steps:**
1. Prepare CSV file
2. Upload via API
3. Validate data
4. Import assignments

**Expected Outcome:**
- Valid data imported
- Invalid data rejected with errors
- Assignments created correctly

---

#### 18. Excel Schedule Export
**File:** `tests/integration/api/test_export_import.py::test_export_schedule_excel_workflow`

**Scenario:**
- Export schedule to Excel
- Include all assignment details
- Faculty can review offline

**Steps:**
1. Request schedule export
2. Specify date range
3. Generate Excel file
4. Download file

**Expected Outcome:**
- Excel file created
- All data included
- File downloadable

---

### 🔐 Authentication & Authorization

#### 19. Role-Based Access Control
**File:** `tests/integration/api/test_auth_workflow.py::test_role_based_access_workflow`

**Scenario:**
- Different user roles have different permissions
- Resident cannot access admin functions
- Faculty can manage own swaps only

**Steps:**
1. Create users with different roles
2. Attempt access to protected resources
3. Verify proper authorization

**Expected Outcome:**
- Admin access granted to admins
- Faculty access limited
- Residents most restricted

---

### 📈 Performance & Load

#### 20. Bulk Import 1000 Assignments
**File:** `tests/integration/scenarios/test_high_load.py::test_bulk_import_1000_assignments_scenario`

**Scenario:**
- Import large dataset at once
- System handles efficiently
- No timeouts or errors

**Steps:**
1. Generate 1000 assignment records
2. Import via bulk API
3. Verify all imported
4. Check performance metrics

**Expected Outcome:**
- Import completes in reasonable time
- No errors
- All data imported correctly

---

### 🔄 Recovery

#### 21. Transaction Rollback
**File:** `tests/integration/scenarios/test_recovery.py::test_transaction_rollback_scenario`

**Scenario:**
- Operation fails mid-transaction
- Database rolls back to consistent state
- No partial data committed

**Steps:**
1. Start transaction
2. Trigger error during operation
3. Verify rollback occurred
4. Check data consistency

**Expected Outcome:**
- Transaction rolled back
- No partial data
- Database consistent

---

#### 22. Swap Rollback
**File:** `tests/integration/scenarios/test_recovery.py::test_swap_rollback_scenario`

**Scenario:**
- Swap executed but needs to be undone
- Within 24-hour rollback window
- Original state restored

**Steps:**
1. Execute swap
2. Request rollback
3. Verify original state restored
4. Check audit trail

**Expected Outcome:**
- Swap rolled back successfully
- Original assignments restored
- Rollback recorded in audit

---

### 🛡️ Data Integrity

#### 23. Referential Integrity
**File:** `tests/integration/scenarios/test_data_integrity.py::test_referential_integrity_scenario`

**Scenario:**
- Attempt to delete person with assignments
- Foreign key constraints enforced
- Cascade or prevent deletion appropriately

**Steps:**
1. Create person with assignments
2. Attempt to delete person
3. Verify constraint enforcement
4. Check assignments status

**Expected Outcome:**
- Deletion prevented or cascaded correctly
- No orphaned records
- Error message if prevented

---

#### 24. Unique Constraint Enforcement
**File:** `tests/integration/scenarios/test_data_integrity.py::test_unique_constraint_scenario`

**Scenario:**
- Attempt to create duplicate email
- Unique constraints enforced
- Clear error message returned

**Steps:**
1. Create person with email
2. Attempt to create another with same email
3. Verify rejection
4. Check error message

**Expected Outcome:**
- Duplicate rejected
- Clear error message
- Original record unchanged

---

## Test Coverage Summary

### By Category

| Category | Test Count | Coverage |
|----------|-----------|----------|
| Schedule Management | 10 | 90%+ |
| Swap Management | 9 | 85%+ |
| ACGME Compliance | 9 | 95%+ |
| Emergency Coverage | 5 | 80%+ |
| Authentication | 10 | 90%+ |
| Import/Export | 8 | 75%+ |
| Reporting | 6 | 70%+ |
| Performance | 3 | 60%+ |
| Recovery | 4 | 80%+ |
| Data Integrity | 4 | 85%+ |

### Priority Levels

#### P0 - Critical (Must Pass)
- Schedule creation
- ACGME compliance validation
- Swap execution
- Authentication
- Data integrity

#### P1 - High (Should Pass)
- Emergency coverage
- Bulk operations
- Import/export
- Reporting

#### P2 - Medium (Nice to Have)
- Performance tests
- Edge cases
- Recovery scenarios

## Running Scenarios

### Run All Scenarios
```bash
pytest tests/integration/scenarios/
```

### Run by Category
```bash
# Emergency scenarios
pytest tests/integration/scenarios/test_emergency_coverage.py

# ACGME enforcement
pytest tests/integration/scenarios/test_acgme_enforcement.py

# Performance
pytest tests/integration/scenarios/test_high_load.py -m slow
```

### Run by Priority
```bash
# Critical tests only
pytest tests/integration/ -m critical

# High priority
pytest tests/integration/ -m "critical or high"
```

## Maintenance

### Adding New Scenarios

1. **Identify use case:** Real-world workflow or edge case
2. **Write scenario:** Following existing patterns
3. **Add to catalog:** Document in this file
4. **Tag appropriately:** Mark priority and category
5. **Update coverage:** Include in coverage metrics

### Reviewing Scenarios

- **Monthly:** Review scenario relevance
- **After incidents:** Add scenarios for production issues
- **Feature releases:** Add scenarios for new features
- **Quarterly:** Archive obsolete scenarios

## Next Steps

- [Integration Testing Guide](./integration-testing-guide.md)
- [E2E Testing Guide](./e2e-testing-guide.md)
- [CI/CD Testing Pipeline](../development/CI_CD_TROUBLESHOOTING.md)
