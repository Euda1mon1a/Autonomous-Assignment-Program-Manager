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

---

***REMOVED******REMOVED*** Karma-Based Allocation

For competitive swaps with multiple interested parties, the system supports a Karma mechanism for fair allocation.

***REMOVED******REMOVED******REMOVED*** How It Works

1. **Initial Balance**: Each provider starts with 100 karma
2. **Bidding**: Providers bid karma on desired swaps
3. **Resolution**: Highest bidder wins the swap
4. **Settlement**: Winner's bid is redistributed to losers

***REMOVED******REMOVED******REMOVED*** Properties

- **Self-contained**: No external currency needed
- **Budget-balanced**: Total karma is conserved
- **Fair**: Losing bids earn karma for future use
- **Equitable**: Gini coefficient monitoring prevents karma concentration

***REMOVED******REMOVED******REMOVED*** Settlement Formula

```
Winner:  K_new = K_old - bid_amount
Losers:  K_new = K_old + (bid_amount / num_losers)
```

***REMOVED******REMOVED******REMOVED*** Related

- **[Advanced Scheduling Architecture](../architecture/advanced-scheduling.md***REMOVED***1-karma-mechanism)** - Full implementation details
- **Service**: `backend/app/services/karma_mechanism.py`

---

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Auto-Find Swap Candidates

```python
def find_swap_candidates(token, faculty_id, week_to_give_away):
    """Find faculty who can swap with given week."""
    ***REMOVED*** Get all faculty
    response = requests.get(
        "http://localhost:8000/api/v1/people",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": "faculty", "active": True}
    )

    faculty = response.json()['items']
    candidates = []

    for candidate in faculty:
        if candidate['id'] == faculty_id:
            continue

        ***REMOVED*** Try validation
        validation = requests.post(
            "http://localhost:8000/api/v1/swaps/validate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_faculty_id": faculty_id,
                "source_week": week_to_give_away,
                "target_faculty_id": candidate['id'],
                "swap_type": "absorb"
            }
        ).json()

        if validation['valid']:
            candidates.append({
                "name": candidate['name'],
                "id": candidate['id'],
                "warnings": validation.get('warnings', [])
            })

    return candidates

***REMOVED*** Usage
candidates = find_swap_candidates(token, faculty_id, "2025-07-15")
print(f"Found {len(candidates)} swap candidates")
```

***REMOVED******REMOVED*** See Also

- [Absences API](absences.md)
- [Quick Reference](../QUICK_REFERENCE.md)
