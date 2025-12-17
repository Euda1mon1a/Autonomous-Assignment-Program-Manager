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
