***REMOVED*** Absence Endpoints

Absence management API endpoints.

---

***REMOVED******REMOVED*** List Absences

<span class="endpoint-badge get">GET</span> `/api/v1/absences`

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `person_id` | uuid | Filter by person |
| `start_date` | date | Filter by start date |
| `end_date` | date | Filter by end date |
| `type` | string | Filter by absence type |

---

***REMOVED******REMOVED*** Get Absence

<span class="endpoint-badge get">GET</span> `/api/v1/absences/{id}`

---

***REMOVED******REMOVED*** Create Absence

<span class="endpoint-badge post">POST</span> `/api/v1/absences`

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "person_id": "uuid",
  "type": "vacation",
  "start_date": "2025-01-15",
  "end_date": "2025-01-20",
  "notes": "Annual vacation"
}
```

---

***REMOVED******REMOVED*** Update Absence

<span class="endpoint-badge put">PUT</span> `/api/v1/absences/{id}`

---

***REMOVED******REMOVED*** Delete Absence

<span class="endpoint-badge delete">DELETE</span> `/api/v1/absences/{id}`
