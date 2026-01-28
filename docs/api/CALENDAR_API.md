# Calendar Export and Subscription API

The Calendar API provides ICS (iCalendar) export and webcal subscription functionality for schedule data. Users can export schedules for import into Google Calendar, Outlook, Apple Calendar, or any other calendar application that supports the ICS format.

## Base URL

```
/calendar
```

## Endpoints Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/calendar/export/ics` | GET | Export all schedules as ICS | No |
| `/calendar/export/ics/{person_id}` | GET | Export person's schedule as ICS | No |
| `/calendar/export/person/{person_id}` | GET | Export person's schedule (alias) | No |
| `/calendar/export/rotation/{rotation_id}` | GET | Export rotation schedule as ICS | No |
| `/calendar/subscribe` | POST | Create calendar subscription | Yes |
| `/calendar/subscribe/{token}` | GET | Get subscription feed (webcal) | No (token-based) |
| `/calendar/subscriptions` | GET | List user's subscriptions | Yes |
| `/calendar/subscribe/{token}` | DELETE | Revoke subscription | Yes |
| `/calendar/feed/{token}` | GET | Legacy subscription endpoint | No (token-based) |

---

## ICS Export Endpoints

### Export All Calendars

**Purpose:** Export complete schedule as an ICS file with optional filtering.

```http
GET /calendar/export/ics?start_date=2024-01-01&end_date=2024-12-31
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date for export (YYYY-MM-DD) |
| `end_date` | date | Yes | End date for export (YYYY-MM-DD) |
| `person_ids` | UUID[] | No | Filter by person UUIDs |
| `rotation_ids` | UUID[] | No | Filter by rotation UUIDs |
| `include_types` | string[] | No | Filter by rotation types |

#### Response

**Content-Type:** `text/calendar`

Downloads an ICS file containing all assignments within the date range. The file is compatible with Google Calendar, Outlook, and Apple Calendar.

**Example filename:** `complete_schedule_2024-01-01_2024-12-31.ics`

#### Example ICS Content

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Residency Scheduler//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:assignment-uuid-1@scheduler.example.com
DTSTAMP:20240115T103000Z
DTSTART:20240120T080000
DTEND:20240120T170000
SUMMARY:Cardiology Clinic
DESCRIPTION:Dr. Smith - Cardiology Clinic
LOCATION:Cardiology Dept
END:VEVENT
END:VCALENDAR
```

#### Error Responses

**500 Internal Server Error**
```json
{
  "detail": "An error occurred generating the calendar"
}
```

#### Notes
- ICS files can be imported once or used for one-time calendar updates
- For automatic updates, use the subscription endpoints instead
- Multiple filters can be combined (person_ids + rotation_ids)

---

### Export Person's Schedule

**Purpose:** Export an individual's schedule as an ICS file.

```http
GET /calendar/export/ics/{person_id}?start_date=2024-01-01&end_date=2024-12-31
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person UUID |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date for export (YYYY-MM-DD) |
| `end_date` | date | Yes | End date for export (YYYY-MM-DD) |
| `include_types` | string[] | No | Filter by rotation types |

#### Response

**Content-Type:** `text/calendar`

Downloads an ICS file containing all assignments for the specified person.

**Example filename:** `schedule_{person_id}_2024-01-01_2024-12-31.ics`

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred generating the calendar"
}
```

#### Notes
- Alternative endpoint: `/calendar/export/person/{person_id}` (same functionality)
- Useful for residents and faculty to import their personal schedules

---

### Export Rotation Calendar

**Purpose:** Export calendar for a specific rotation showing all assigned personnel.

```http
GET /calendar/export/rotation/{rotation_id}?start_date=2024-01-01&end_date=2024-12-31
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `rotation_id` | UUID | Rotation template UUID |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date for export (YYYY-MM-DD) |
| `end_date` | date | Yes | End date for export (YYYY-MM-DD) |

#### Response

**Content-Type:** `text/calendar`

Downloads an ICS file containing all assignments for the specified rotation.

**Example filename:** `rotation_{rotation_id}_2024-01-01_2024-12-31.ics`

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred generating the calendar"
}
```

#### Notes
- Useful for rotation coordinators to see who is assigned
- Shows all personnel assignments for a given rotation

---

## Webcal Subscription Endpoints

### Create Calendar Subscription

**Purpose:** Generate a secure token for calendar feed subscriptions with automatic updates.

```http
POST /calendar/subscribe
```

**Authentication:** Required (JWT)

#### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "label": "My Work Schedule",
  "expires_days": 365
}
```

**Schema:** `CalendarSubscriptionCreate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person UUID to subscribe to |
| `label` | string | No | Optional label (max 255 chars) |
| `expires_days` | integer | No | Days until expiration (1-365, null = never) |

#### Response

**Status:** 201 Created

```json
{
  "token": "abc123def456",
  "subscription_url": "https://api.example.com/api/calendar/subscribe/abc123def456",
  "webcal_url": "webcal://api.example.com/api/calendar/subscribe/abc123def456",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "label": "My Work Schedule",
  "created_at": "2024-01-15T10:30:00.000000",
  "expires_at": "2025-01-15T10:30:00.000000",
  "last_accessed_at": null,
  "is_active": true
}
```

**Schema:** `CalendarSubscriptionResponse`

#### How to Use

1. Copy the `webcal_url` from the response
2. Paste it into your calendar app:
   - **Google Calendar:** Settings → Add calendar → From URL
   - **Outlook:** Open Calendar → Add calendar → Subscribe from web
   - **Apple Calendar:** File → New Calendar Subscription
3. Your calendar will automatically refresh with schedule updates (typically every 15-60 minutes)

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred creating the subscription"
}
```

#### Notes
- Subscription tokens are secure and unguessable
- Each token is unique and can be revoked
- Calendar apps poll the feed periodically (typically every 15-60 minutes)

---

### Get Subscription Feed

**Purpose:** Webcal endpoint that calendar applications call to fetch updates.

```http
GET /calendar/subscribe/{token}
```

**Authentication:** No (token serves as authentication)

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | string | Subscription token from creation endpoint |

#### Response

**Content-Type:** `text/calendar; charset=utf-8`

Returns ICS calendar content with:
- All assignments from today through 6 months in the future
- Proper VTIMEZONE for America/New_York
- Event details including location, notes, and role

**Headers:**
- `Cache-Control: private, max-age=900` (15-minute refresh suggestion)
- `X-Content-Type-Options: nosniff` (prevent proxy transformation)

#### Error Responses

**401 Unauthorized**
```json
{
  "detail": "Invalid or expired subscription token. Please generate a new subscription."
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred generating the calendar feed"
}
```

#### Notes
- This endpoint is called automatically by calendar applications
- No authentication header needed - token in URL serves as auth
- Calendar apps typically poll every 15-60 minutes
- Feed includes 6 months of future data by default

---

### List Subscriptions

**Purpose:** Retrieve all calendar subscriptions created by the current user.

```http
GET /calendar/subscriptions?person_id={uuid}&active_only=true
```

**Authentication:** Required (JWT)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `person_id` | UUID | null | Optional filter by person |
| `active_only` | boolean | true | Only show active subscriptions |

#### Response

**Status:** 200 OK

```json
{
  "subscriptions": [
    {
      "token": "abc123def456",
      "subscription_url": "https://api.example.com/api/calendar/subscribe/abc123def456",
      "webcal_url": "webcal://api.example.com/api/calendar/subscribe/abc123def456",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "label": "My Work Schedule",
      "created_at": "2024-01-15T10:30:00.000000",
      "expires_at": "2025-01-15T10:30:00.000000",
      "last_accessed_at": "2024-01-15T14:30:00.000000",
      "is_active": true
    }
  ],
  "total": 1
}
```

**Schema:** `CalendarSubscriptionListResponse`

#### Notes
- Shows subscriptions created by the current user only
- Use `last_accessed_at` to see if the subscription is being used
- Inactive subscriptions can be filtered out with `active_only=true`

---

### Revoke Subscription

**Purpose:** Permanently disable a calendar subscription token.

```http
DELETE /calendar/subscribe/{token}
```

**Authentication:** Required (JWT)

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | string | Subscription token to revoke |

#### Response

**Status:** 204 No Content

No response body. Calendar apps using this subscription will no longer receive updates.

#### Error Responses

**403 Forbidden**
```json
{
  "detail": "Not authorized to revoke this subscription"
}
```

**404 Not Found**
```json
{
  "detail": "Subscription not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to revoke subscription"
}
```

#### Notes
- Only the user who created the subscription can revoke it
- Revocation is permanent - the token cannot be reactivated
- Calendar apps will receive 401 errors when trying to fetch the feed

---

## Legacy Endpoint

### Get Subscription Feed (Legacy)

```http
GET /calendar/feed/{token}
```

Redirects to `/calendar/subscribe/{token}`. Maintained for backward compatibility.

---

## Calendar Integration Examples

### Google Calendar

1. Open Google Calendar
2. Click the "+" next to "Other calendars"
3. Select "From URL"
4. Paste the `webcal_url` from the subscription response
5. Click "Add calendar"

### Outlook

1. Open Outlook Calendar
2. Right-click "My Calendars"
3. Select "Add calendar" → "Subscribe from web"
4. Paste the `webcal_url`
5. Click "Import"

### Apple Calendar

1. Open Calendar app
2. File → New Calendar Subscription
3. Paste the `webcal_url`
4. Click "Subscribe"
5. Configure refresh frequency (recommended: every 15-30 minutes)

---

## ICS File Format Details

### Event Fields

| Field | Description |
|-------|-------------|
| `UID` | Unique identifier for the event |
| `DTSTAMP` | Timestamp when event was created |
| `DTSTART` | Event start time |
| `DTEND` | Event end time |
| `SUMMARY` | Event title (rotation name) |
| `DESCRIPTION` | Event details (person name, rotation, notes) |
| `LOCATION` | Event location (department, clinic, etc.) |

### Timezone Handling

- All events include VTIMEZONE for America/New_York
- Times are exported in local timezone
- Calendar apps handle conversion to user's timezone automatically

---

## Security Considerations

### Token Security

- Subscription tokens are cryptographically secure random strings
- Tokens should be treated like passwords (do not share)
- Revoke tokens if compromised
- Set expiration dates for temporary access

### Access Control

- Users can only create subscriptions for themselves (enforced by authentication)
- Subscription tokens provide read-only access
- No sensitive data (SSN, medical records) included in calendar events

### HTTPS Enforcement

- All subscription URLs use HTTPS in production
- `webcal://` protocol is automatically converted to HTTPS by calendar apps
- HTTP requests are upgraded to HTTPS

---

## Related Documentation

- `backend/app/api/routes/calendar.py` - Implementation
- `backend/app/services/calendar_service.py` - Business logic
- `backend/app/schemas/calendar.py` - Request/response schemas
- [RFC 5545](https://tools.ietf.org/html/rfc5545) - iCalendar specification
