# Swap Marketplace

The swap system allows residents to trade assignments.

---

## Requesting a Swap

1. Navigate to **Swap Marketplace**
2. Click **Request Swap**
3. Select:
    - **Your Assignment**: The block you want to trade
    - **Preferred Dates**: When you'd prefer to work
    - **Notes**: Additional context
4. Click **Submit Request**

---

## Auto-Matching

The system automatically finds compatible swaps using a 5-factor algorithm:

1. **Availability**: Both parties available
2. **Preferences**: Match preferences
3. **Specialization**: Required skills match
4. **PGY Balance**: Appropriate experience levels
5. **Coverage Impact**: Maintains adequate coverage

---

## Responding to Swap Requests

1. View incoming requests in your dashboard
2. Click **View Details** on a request
3. Review:
    - Assignment details
    - Impact on your schedule
    - Compliance status
4. Click **Accept** or **Decline**

---

## Swap Status

| Status | Description |
|--------|-------------|
| **Pending** | Awaiting response |
| **Matched** | Found potential match |
| **Accepted** | Both parties agreed |
| **Completed** | Swap executed |
| **Cancelled** | Request withdrawn |
| **Declined** | Request rejected |

---

## Marketplace Access Control

The swap marketplace is controlled by a feature flag (`swap_marketplace_enabled`) to prevent gamification of the swap system.

### Default Access

| Role | Marketplace Access |
|------|-------------------|
| **Admin** | Full access |
| **Coordinator** | Full access |
| **Faculty** | Full access |
| **Resident** | **Disabled by default** |

### Why Residents Are Restricted

Residents are blocked from the marketplace by default to prevent exploitation of post-call rules. For example:
- Faculty A had call, so automatically has PCAT + DO the next day
- Without restrictions, residents could use swaps to strategically avoid clinic half-days
- This could lead to unfair distribution of less desirable shifts

### Enabling Marketplace for Residents

Administrators can enable marketplace access for residents via the Feature Flags API:

```bash
# Enable for all residents
curl -X PUT /api/v1/features/swap_marketplace_enabled \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"target_roles": ["admin", "coordinator", "faculty", "resident"]}'

# Enable for specific residents only
curl -X PUT /api/v1/features/swap_marketplace_enabled \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"target_user_ids": ["user-uuid-1", "user-uuid-2"]}'
```

### Direct Swaps Still Allowed

Even when marketplace access is disabled, residents can still:
- Request direct swaps with a specific faculty member (one-to-one swaps)
- Respond to swap requests directed at them
- View their own swap history

Only marketplace browsing and open posting are restricted.

---

## ACGME Compliance

All swaps are validated against ACGME rules:

- 80-hour week limits
- 1-in-7 day off requirements
- Supervision ratios
- Continuous duty limits

!!! danger "Compliance Violations"
    Swaps that would create ACGME violations are blocked automatically.

---

## Related Documentation

- **[Swap Management Guide](../guides/swap-management.md)** - Detailed swap workflow guide
- **[User Workflows](../guides/user-workflows.md)** - Complete user guide with swap examples
- **[Compliance Monitoring](compliance.md)** - Understanding ACGME compliance
- **[API: Swaps](../api/swaps.md)** - Swap API documentation
