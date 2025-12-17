# Swap Endpoints

Swap marketplace API endpoints.

---

## List Swap Requests

<span class="endpoint-badge get">GET</span> `/api/v1/swaps`

### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `status` | string | Filter by status |
| `requester_id` | uuid | Filter by requester |

---

## Get Swap Request

<span class="endpoint-badge get">GET</span> `/api/v1/swaps/{id}`

---

## Create Swap Request

<span class="endpoint-badge post">POST</span> `/api/v1/swaps`

### Request

```json
{
  "assignment_id": "uuid",
  "preferred_dates": ["2025-01-20", "2025-01-21"],
  "notes": "Need to swap due to personal commitment"
}
```

---

## Accept Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/{id}/accept`

---

## Decline Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/{id}/decline`

---

## Cancel Swap

<span class="endpoint-badge delete">DELETE</span> `/api/v1/swaps/{id}`
