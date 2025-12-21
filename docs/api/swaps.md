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

---

## Karma-Based Allocation

For competitive swaps with multiple interested parties, the system supports a Karma mechanism for fair allocation.

### How It Works

1. **Initial Balance**: Each provider starts with 100 karma
2. **Bidding**: Providers bid karma on desired swaps
3. **Resolution**: Highest bidder wins the swap
4. **Settlement**: Winner's bid is redistributed to losers

### Properties

- **Self-contained**: No external currency needed
- **Budget-balanced**: Total karma is conserved
- **Fair**: Losing bids earn karma for future use
- **Equitable**: Gini coefficient monitoring prevents karma concentration

### Settlement Formula

```
Winner:  K_new = K_old - bid_amount
Losers:  K_new = K_old + (bid_amount / num_losers)
```

### Related

- **[Advanced Scheduling Architecture](../architecture/advanced-scheduling.md#1-karma-mechanism)** - Full implementation details
- **Service**: `backend/app/services/karma_mechanism.py`
