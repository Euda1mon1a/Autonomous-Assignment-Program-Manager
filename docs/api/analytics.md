***REMOVED*** Analytics Endpoints

Reporting and analytics API endpoints.

---

***REMOVED******REMOVED*** Coverage Metrics

<span class="endpoint-badge get">GET</span> `/api/v1/analytics/coverage`

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `start_date` | date | Analysis start |
| `end_date` | date | Analysis end |

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "coverage_rate": 0.95,
  "gaps": [
    {
      "date": "2025-01-15",
      "period": "AM",
      "missing_roles": ["resident"]
    }
  ]
}
```

---

***REMOVED******REMOVED*** Compliance Metrics

<span class="endpoint-badge get">GET</span> `/api/v1/analytics/compliance`

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "compliance_rate": 0.98,
  "violations": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 10
  }
}
```

---

***REMOVED******REMOVED*** Fairness Metrics

<span class="endpoint-badge get">GET</span> `/api/v1/analytics/fairness`

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "fairness_index": 0.92,
  "distribution": {
    "min_hours": 38,
    "max_hours": 45,
    "avg_hours": 41.5,
    "std_dev": 2.1
  }
}
```

---

***REMOVED******REMOVED*** What-If Analysis

<span class="endpoint-badge post">POST</span> `/api/v1/analytics/what-if`

Analyze impact of hypothetical changes.

---

***REMOVED******REMOVED*** Quick Examples

***REMOVED******REMOVED******REMOVED*** Get System Statistics

```bash
curl "http://localhost:8000/api/v1/analytics/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

***REMOVED******REMOVED******REMOVED*** View Compliance Metrics

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/analytics/compliance",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "start_date": "2025-07-01",
        "end_date": "2025-09-30"
    }
)

metrics = response.json()
print(f"80-Hour Violations: {metrics['violations_80_hour']}")
print(f"1-in-7 Violations: {metrics['violations_1_in_7']}")
```

***REMOVED******REMOVED*** See Also

- [Compliance API](endpoints/compliance.md) - ACGME validation
- [Schedules API](endpoints/schedules.md) - Schedule management
- [Metrics Guide](../operations/metrics.md) - Metrics documentation
