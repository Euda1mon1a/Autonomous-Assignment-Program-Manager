# People Endpoints

Personnel management API endpoints.

---

## List People

<span class="endpoint-badge get">GET</span> `/api/v1/people`

### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `type` | string | Filter by type (resident, faculty) |
| `pgy_level` | integer | Filter by PGY level |
| `active` | boolean | Filter by active status |

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "type": "resident",
      "pgy_level": 2,
      "specialty": "Family Medicine"
    }
  ],
  "total": 50
}
```

---

## Get Person

<span class="endpoint-badge get">GET</span> `/api/v1/people/{id}`

---

## Create Person

<span class="endpoint-badge post">POST</span> `/api/v1/people`

### Request

```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "type": "resident",
  "pgy_level": 1,
  "specialty": "Family Medicine"
}
```

---

## Update Person

<span class="endpoint-badge put">PUT</span> `/api/v1/people/{id}`

---

## Delete Person

<span class="endpoint-badge delete">DELETE</span> `/api/v1/people/{id}`
