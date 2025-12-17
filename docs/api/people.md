***REMOVED*** People Endpoints

Personnel management API endpoints.

---

***REMOVED******REMOVED*** List People

<span class="endpoint-badge get">GET</span> `/api/v1/people`

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `type` | string | Filter by type (resident, faculty) |
| `pgy_level` | integer | Filter by PGY level |
| `active` | boolean | Filter by active status |

***REMOVED******REMOVED******REMOVED*** Response

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

***REMOVED******REMOVED*** Get Person

<span class="endpoint-badge get">GET</span> `/api/v1/people/{id}`

---

***REMOVED******REMOVED*** Create Person

<span class="endpoint-badge post">POST</span> `/api/v1/people`

***REMOVED******REMOVED******REMOVED*** Request

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

***REMOVED******REMOVED*** Update Person

<span class="endpoint-badge put">PUT</span> `/api/v1/people/{id}`

---

***REMOVED******REMOVED*** Delete Person

<span class="endpoint-badge delete">DELETE</span> `/api/v1/people/{id}`
