***REMOVED*** Swap Endpoints

Swap marketplace API endpoints.

---

***REMOVED******REMOVED*** List Swap Requests

<span class="endpoint-badge get">GET</span> `/api/v1/swaps`

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `status` | string | Filter by status |
| `requester_id` | uuid | Filter by requester |

---

***REMOVED******REMOVED*** Get Swap Request

<span class="endpoint-badge get">GET</span> `/api/v1/swaps/{id}`

---

***REMOVED******REMOVED*** Create Swap Request

<span class="endpoint-badge post">POST</span> `/api/v1/swaps`

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "assignment_id": "uuid",
  "preferred_dates": ["2025-01-20", "2025-01-21"],
  "notes": "Need to swap due to personal commitment"
}
```

---

***REMOVED******REMOVED*** Accept Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/{id}/accept`

---

***REMOVED******REMOVED*** Decline Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/{id}/decline`

---

***REMOVED******REMOVED*** Cancel Swap

<span class="endpoint-badge delete">DELETE</span> `/api/v1/swaps/{id}`
