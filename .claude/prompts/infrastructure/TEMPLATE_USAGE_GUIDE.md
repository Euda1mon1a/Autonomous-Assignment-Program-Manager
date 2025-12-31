***REMOVED*** Template Usage Guide

> **Version:** 1.0
> **Purpose:** Complete guide for using prompt templates effectively

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** 1. Find Your Template
- Determine agent type (G-Staff, Development, Specialist, or Probe)
- Find template file in `.claude/prompts/agents/` or `.claude/prompts/probes/`
- Select appropriate template from file

***REMOVED******REMOVED******REMOVED*** 2. Initialize Variables
Copy template and replace all `${VARIABLE}` placeholders:
```
Before:
**MISSION:** ${MISSION_OBJECTIVE}
**PERSONNEL:** ${PERSONNEL_COUNT}

After:
**MISSION:** Generate schedule for Q4 2025
**PERSONNEL:** 45
```

***REMOVED******REMOVED******REMOVED*** 3. Execute
Follow the step-by-step process in the template.

***REMOVED******REMOVED******REMOVED*** 4. Report
Use Status Report template to communicate outcomes.

---

***REMOVED******REMOVED*** Template Selection Guide

***REMOVED******REMOVED******REMOVED*** By Scenario

**Need to generate schedule?**
→ G5 Planning → Schedule Generation Template

**Need to execute schedule?**
→ G3 Operations → Assignment Execution Template

**Need to resolve conflict?**
→ G3 Operations → Conflict Resolution Template

**Need to process swap?**
→ Swap Coordinator → Swap Request Processing Template

**Need to audit compliance?**
→ ACGME Validator → Compliance Validation Template

**Need to analyze threats?**
→ G2 Recon → Threat Assessment Template

**Need to find hidden issues?**
→ Stealth Probe → Hidden Vulnerability Discovery Template

---

***REMOVED******REMOVED*** Variable Initialization Workflow

***REMOVED******REMOVED******REMOVED*** Step 1: Extract Variables
```bash
***REMOVED*** List all variables in template
grep -o '\${[^}]*}' template.md | sort -u
```

***REMOVED******REMOVED******REMOVED*** Step 2: Gather Data
Collect actual values for each variable from:
- Database queries
- API calls
- System metrics
- Configuration files

***REMOVED******REMOVED******REMOVED*** Step 3: Sanitize Sensitive Data
- Replace person names with IDs
- Remove specific location details
- Mask dates for OPSEC
- Exclude sensitive information

***REMOVED******REMOVED******REMOVED*** Step 4: Validate Types
Ensure each variable:
- Matches expected type (int, string, date, etc)
- Falls within valid range
- Uses correct format
- Is not null/undefined

***REMOVED******REMOVED******REMOVED*** Step 5: Substitute
Replace all `${VARIABLE}` with actual values:
```python
template = template.replace("${PERSON_ID}", "A1B2C3D4")
template = template.replace("${COVERAGE_PERCENT}", "92")
```

---

***REMOVED******REMOVED*** Common Issues & Solutions

***REMOVED******REMOVED******REMOVED*** Issue: "Variable not initialized"
**Solution:** Check template for all `${VARIABLES}` and ensure each has a value

***REMOVED******REMOVED******REMOVED*** Issue: "ACGME violation detected"
**Solution:** Re-run ACGME compliance check, adjust schedule, validate again

***REMOVED******REMOVED******REMOVED*** Issue: "Timeout during execution"
**Solution:** Check time limit, optimize query performance, reduce scope

***REMOVED******REMOVED******REMOVED*** Issue: "Missing required output"
**Solution:** Verify all template steps completed, check error logs

***REMOVED******REMOVED******REMOVED*** Issue: "Escalation threshold reached"
**Solution:** Expected behavior - escalate to human leadership per template

---

***REMOVED******REMOVED*** Best Practices

1. **Always initialize ALL variables** before execution
2. **Use consistent formatting** for dates, times, numbers
3. **Sanitize sensitive data** before storage/reporting
4. **Log all important steps** for audit trail
5. **Validate ACGME compliance** at each critical point
6. **Test templates** with sample data first
7. **Archive completed templates** for compliance
8. **Monitor performance** against baselines
9. **Update variables dynamically** from live data
10. **Document any deviations** from standard process

---

***REMOVED******REMOVED*** Template Reuse Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Status Reporting Loop
```
1. Execute mission template
2. Collect metrics
3. Run Status Report template
4. Schedule next cycle
5. Archive report
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Multi-Step Workflow
```
1. Run Intelligence template (G2)
2. Run Planning template (G5/G1)
3. Run Operations template (G3)
4. Run Communication template (G6)
5. Collect results
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Error Recovery
```
1. Execute mission
2. IF error detected:
   a. Run Error Handling template
   b. Execute recovery steps
   c. Re-run mission
3. Continue
```

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Debug Checklist
- [ ] All variables initialized
- [ ] Variable types correct
- [ ] Variable values realistic
- [ ] ACGME constraints satisfied
- [ ] Time limits sufficient
- [ ] Resources available
- [ ] Permissions correct
- [ ] Error handling active

***REMOVED******REMOVED******REMOVED*** Debug Output
```
**DEBUG INFO:**
- Template: ${TEMPLATE_NAME}
- Variables initialized: ${INIT_COUNT}/${TOTAL_COUNT}
- Compliance status: ${COMPLIANCE_CHECK}
- Time remaining: ${TIME_REMAINING}s
- Last successful step: ${LAST_SUCCESS}
```

---

***REMOVED******REMOVED*** Performance Tips

1. **Pre-compile complex templates** before variable substitution
2. **Cache frequently accessed variables** (personnel list, metrics)
3. **Use parallel templates** for independent operations
4. **Set realistic timeouts** (not too strict, not too loose)
5. **Monitor template execution** in real-time
6. **Profile slow templates** and optimize bottlenecks

---

***REMOVED******REMOVED*** Advanced Usage

***REMOVED******REMOVED******REMOVED*** Conditional Templates
Use IF/THEN logic to select templates:
```
IF ${COMPLIANCE_STATUS} == VIOLATIONS:
  Execute remediation_template
ELSE:
  Execute confirmation_template
```

***REMOVED******REMOVED******REMOVED*** Nested Templates
Compose complex workflows from simpler templates:
```
Main mission
├─ Validate constraints
├─ Generate schedule
├─ Validate compliance
└─ Report results
```

***REMOVED******REMOVED******REMOVED*** Dynamic Variable Injection
Update variables during execution:
```
Initial: ${COVERAGE_PERCENT} = 85
After optimization: ${COVERAGE_PERCENT} = 92
```

---

***REMOVED******REMOVED*** Support Resources

- **Quick reference:** See PROMPT_TEMPLATE_INDEX.md
- **Variable guide:** See TEMPLATE_VARIABLES.md
- **Validation rules:** See TEMPLATE_VALIDATION.md
- **Performance info:** See TEMPLATE_PERFORMANCE.md
- **Composition patterns:** See TEMPLATE_COMPOSITION.md

---

***REMOVED******REMOVED*** Feedback & Improvement

To improve templates:
1. Document what didn't work
2. Describe expected behavior
3. Suggest modifications
4. Submit feedback to development lead

---

*Last Updated: 2025-12-31*
*Questions? See PROMPT_TEMPLATE_INDEX.md for full documentation*
