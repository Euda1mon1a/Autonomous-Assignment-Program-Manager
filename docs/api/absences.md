# Absence Endpoints

Absence management API endpoints.

---

## List Absences

<span class="endpoint-badge get">GET</span> `/api/v1/absences`

### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `person_id` | uuid | Filter by person |
| `start_date` | date | Filter by start date |
| `end_date` | date | Filter by end date |
| `type` | string | Filter by absence type |

---

## Get Absence

<span class="endpoint-badge get">GET</span> `/api/v1/absences/{id}`

---

## Create Absence

<span class="endpoint-badge post">POST</span> `/api/v1/absences`

### Request

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

## Update Absence

<span class="endpoint-badge put">PUT</span> `/api/v1/absences/{id}`

---

## Delete Absence

<span class="endpoint-badge delete">DELETE</span> `/api/v1/absences/{id}`
