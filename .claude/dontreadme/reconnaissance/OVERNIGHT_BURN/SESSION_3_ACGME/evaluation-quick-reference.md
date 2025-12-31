# ACGME Program Evaluation - Quick Reference

**Quick Navigation for Program Directors & Coordinators**

---

## Essential Metrics At A Glance

### Compliance Status
| Rule | Target | Current Path | Status |
|------|--------|----------------|--------|
| 80-Hour Rule | 100% residents | Dashboard → Compliance | Monitored |
| 1-in-7 Rule | 100% residents | Dashboard → Compliance | Monitored |
| Supervision Ratios | 100% blocks | Dashboard → Supervision | Monitored |
| Coverage Rate | ≥95% blocks | Dashboard → Coverage | Monitored |

---

## Key System Locations

### Compliance Reporting
- **PDF Reports:** `backend/app/compliance/reports.py`
- **Excel Data Export:** `ComplianceReportGenerator.export_to_excel()`
- **Automated Monthly:** Configure in compliance_report_tasks.py

### Real-Time Dashboards
- **Grafana:** `localhost:3000` (when running `docker-compose up`)
- **Dashboard Builder:** `backend/app/core/metrics/dashboards.py`
- **Prometheus Metrics:** `localhost:9090/metrics`

### Violation Tracking
- **Detection:** `backend/app/scheduling/validator.py`
- **Logging:** Automatically recorded in audit_log
- **Alerts:** Sent to compliance team within 24 hours

---

## Common Tasks

### Monthly Compliance Review
```bash
# Generate monthly compliance report
curl -X GET "http://localhost:8000/api/v1/analytics/compliance" \
  -H "Authorization: Bearer TOKEN"

# Or via Python
from app.compliance.reports import ComplianceReportGenerator
generator = ComplianceReportGenerator(db)
report = generator.generate_compliance_data(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)
pdf_bytes = generator.export_to_pdf(report)
```

### Investigate a Violation
```
1. Check violation in audit log
2. Review resident's assignments for that period
3. Check for absences (might impact hours)
4. Verify supervisor contacts were made
5. Document remediation plan
6. Mark as resolved once corrected
```

### Prepare for Site Visit
```
30 days before:
1. Pull 12-month compliance report
2. Extract key metrics summary
3. Identify any unresolved violations
4. Prepare educational outcome data
5. Compile any improvement projects
6. Review feedback from residents/faculty

Week of visit:
1. Have dashboards ready for demonstration
2. Print recent compliance reports
3. Have audit logs available
4. Prepare explanations for any anomalies
5. Coordinate with faculty on interview questions
```

### Respond to a Citation
```
Within 24 hours:
1. Document what caused the violation
2. Notify compliance team
3. Plan corrective action

Within 30 days:
1. Implement corrective action
2. Collect evidence of change
3. Monitor for improvement
4. Compile response package
5. Submit to accreditor

Ongoing:
1. Weekly monitoring (not just monthly)
2. Report progress to PD
3. Keep accreditor informed
```

---

## Key Reports & Where to Find Them

| Report | Location | Frequency | Users |
|--------|----------|-----------|-------|
| Compliance Summary | Dashboard → Summary Stat | Real-time | All |
| 80-Hour Analysis | Compliance Report (PDF) | Monthly | PD, Coord |
| 1-in-7 Analysis | Compliance Report (PDF) | Monthly | PD, Coord |
| Supervision Coverage | Compliance Report (PDF) | Monthly | PD, APD |
| Fairness Analysis | Dashboard → Workload | Weekly | Scheduler |
| Leave Utilization | Excel Export | Quarterly | HR |
| Educational Outcomes | Quality Report (PDF) | Annually | PD, ADEA |
| Site Visit Package | Evidence Compiler | On-demand | PD |

---

## Alert Escalation

### What Triggers Alerts

**CRITICAL (Page immediately):**
- Work hour violation (80+ hours in any week)
- Supervision ratio violation (block uncovered)
- Multiple violations in 30 days (>3)

**HIGH (Email within 1 hour):**
- Compliance rate drops below 95%
- Fairness index drops below 0.85
- Absence > 10% of workdays

**MEDIUM (Daily digest):**
- Compliance rate 95-98%
- Fairness index 0.85-0.90
- Schedule coverage < 95%

**INFO (Weekly report):**
- Routine metrics updates
- Trend analysis
- Improvement project progress

### Responding to Alerts

1. **CRITICAL:** Immediate action required
   - Contact PD and coordinator
   - Investigate root cause
   - Execute remediation (same day)

2. **HIGH:** Action within 24 hours
   - Review contributing factors
   - Plan corrective measures
   - Begin implementation

3. **MEDIUM:** Addressed in routine cycle
   - Monitor trend
   - Plan improvement
   - Track progress

---

## Useful Queries

### Most Recent Violations
```bash
# Via API
GET /api/v1/analytics/compliance?violations_only=true

# Via SQL (if available)
SELECT * FROM violations
ORDER BY detected_date DESC
LIMIT 10;
```

### Resident with Most Violations
```python
from sqlalchemy import func
from app.models.violation import Violation

violations_by_resident = db.query(
    Violation.resident_id,
    func.count(Violation.id).label('violation_count')
).group_by(
    Violation.resident_id
).order_by(
    func.count(Violation.id).desc()
).all()
```

### Blocks Without Supervision Coverage
```python
from app.models.assignment import Assignment
from app.models.block import Block

# Find blocks with insufficient faculty
blocks_with_issues = identify_supervision_gaps(db)
```

---

## Dashboard Quick Tips

### Accessing Dashboards
1. Open browser → `http://localhost:3000`
2. Login (default: admin/admin, change in production)
3. Select dashboard from list

### Setting Up Alerts
1. Dashboard → Alert Rules
2. Add new rule (e.g., "Compliance < 95%")
3. Configure notification channels (email, Slack)
4. Set escalation (who to notify, when)

### Exporting Data
1. Panel → ... menu → Export as CSV/JSON
2. Or use API `/api/v1/metrics/export`

---

## Troubleshooting

### "No data showing in dashboard"
- Check date range (top left)
- Verify metrics are being collected (`/metrics/health`)
- Check Prometheus connection (`localhost:9090`)

### "Compliance report shows zero violations but PD says there are some"
- May be generating report before assignments created
- Check date range includes assignment date
- Verify validator is running on schedule

### "Violation detected but alert not sent"
- Check alert notification channel configuration
- Verify email/Slack credentials
- Check alert rules are enabled
- Review alert logs

### "Fairness metrics seem wrong"
- May need to recalculate (refresh dashboard)
- Check if all assignments are included
- Verify absences aren't double-counted

---

## Contact & Support

**For System Issues:**
- Scheduler Administrator
- Compliance Officer

**For Accreditation Questions:**
- Program Director
- ACGME Liaison

**For Technical Details:**
- See full documentation: `acgme-program-evaluation.md`

---

**Last Updated:** 2025-12-30
**Document Type:** Quick Reference
**Full Documentation:** See `acgme-program-evaluation.md` for comprehensive details
