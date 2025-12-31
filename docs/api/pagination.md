***REMOVED*** Pagination Reference

Complete guide to pagination patterns in the Residency Scheduler API.

---

***REMOVED******REMOVED*** Overview

List endpoints that return multiple items support pagination to limit response size and improve performance.

---

***REMOVED******REMOVED*** Pagination Parameters

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | integer | 1 | 1-∞ | Page number (1-indexed) |
| `page_size` | integer | 100 | 1-500 | Items per page |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl "http://localhost:8000/api/v1/assignments?page=2&page_size=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED*** Response Format

***REMOVED******REMOVED******REMOVED*** Paginated Response Structure

```json
{
  "items": [...],
  "total": 248,
  "page": 2,
  "page_size": 50,
  "pages": 5
}
```

***REMOVED******REMOVED******REMOVED*** Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | Array of resources for current page |
| `total` | integer | Total number of items across all pages |
| `page` | integer | Current page number |
| `page_size` | integer | Items per page |
| `pages` | integer | Total number of pages |

---

***REMOVED******REMOVED*** Response Headers

***REMOVED******REMOVED******REMOVED*** Pagination Headers

```http
X-Total-Count: 248
X-Page: 2
X-Page-Size: 50
X-Total-Pages: 5
Link: <http://localhost:8000/api/v1/assignments?page=1&page_size=50>; rel="first",
      <http://localhost:8000/api/v1/assignments?page=3&page_size=50>; rel="next",
      <http://localhost:8000/api/v1/assignments?page=5&page_size=50>; rel="last",
      <http://localhost:8000/api/v1/assignments?page=1&page_size=50>; rel="prev"
```

***REMOVED******REMOVED******REMOVED*** Header Descriptions

| Header | Description |
|--------|-------------|
| `X-Total-Count` | Total items across all pages |
| `X-Page` | Current page number |
| `X-Page-Size` | Items per page |
| `X-Total-Pages` | Total number of pages |
| `Link` | RFC 5988 Link header with pagination links |

***REMOVED******REMOVED******REMOVED*** Link Header Relations

| Relation | Description |
|----------|-------------|
| `first` | First page |
| `prev` | Previous page (omitted on first page) |
| `next` | Next page (omitted on last page) |
| `last` | Last page |

---

***REMOVED******REMOVED*** Endpoints with Pagination

***REMOVED******REMOVED******REMOVED*** Assignments

**Endpoint**: `GET /api/v1/assignments`

**Default page_size**: 100

**Max page_size**: 500

**Example**:
```bash
curl "http://localhost:8000/api/v1/assignments?page=1&page_size=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED******REMOVED*** Swap History

**Endpoint**: `GET /api/v1/swaps/history`

**Default page_size**: 20

**Max page_size**: 100

**Example**:
```bash
curl "http://localhost:8000/api/v1/swaps/history?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED******REMOVED*** Health Check History

**Endpoint**: `GET /api/v1/resilience/health/history`

**Default page_size**: 100

**Max page_size**: 500

**Example**:
```bash
curl "http://localhost:8000/api/v1/resilience/health/history?page=1&page_size=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED******REMOVED*** Event History

**Endpoint**: `GET /api/v1/resilience/events`

**Default page_size**: 100

**Max page_size**: 500

**Example**:
```bash
curl "http://localhost:8000/api/v1/resilience/events?page=1&page_size=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED*** Pagination Patterns

***REMOVED******REMOVED******REMOVED*** 1. Iterating Through All Pages

**Python Example**:

```python
import requests

def get_all_assignments(token):
    """Fetch all assignments across all pages."""
    all_assignments = []
    page = 1
    page_size = 100

    while True:
        response = requests.get(
            "http://localhost:8000/api/v1/assignments",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": page, "page_size": page_size}
        )

        data = response.json()
        all_assignments.extend(data['items'])

        ***REMOVED*** Check if more pages
        if page >= data['pages']:
            break

        page += 1

    return all_assignments

***REMOVED*** Usage
assignments = get_all_assignments(token)
print(f"Total assignments: {len(assignments)}")
```

**JavaScript Example**:

```javascript
async function getAllAssignments(token) {
  const allAssignments = [];
  let page = 1;
  const pageSize = 100;

  while (true) {
    const response = await fetch(
      `http://localhost:8000/api/v1/assignments?page=${page}&page_size=${pageSize}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    allAssignments.push(...data.items);

    // Check if more pages
    if (page >= data.pages) {
      break;
    }

    page++;
  }

  return allAssignments;
}

// Usage
const assignments = await getAllAssignments(token);
console.log(`Total assignments: ${assignments.length}`);
```

---

***REMOVED******REMOVED******REMOVED*** 2. Using Link Headers for Navigation

**Python Example**:

```python
import requests
from requests.utils import parse_header_links

def get_next_page_url(response):
    """Extract next page URL from Link header."""
    link_header = response.headers.get('Link')
    if not link_header:
        return None

    links = parse_header_links(link_header)
    for link in links:
        if link.get('rel') == 'next':
            return link.get('url')

    return None

***REMOVED*** Fetch pages using Link header
url = "http://localhost:8000/api/v1/assignments?page=1&page_size=50"
all_assignments = []

while url:
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    all_assignments.extend(data['items'])

    url = get_next_page_url(response)

print(f"Total assignments: {len(all_assignments)}")
```

---

***REMOVED******REMOVED******REMOVED*** 3. Implementing Client-Side Pagination

**React Example with TanStack Query**:

```javascript
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

function AssignmentList() {
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading, error } = useQuery({
    queryKey: ['assignments', page, pageSize],
    queryFn: async () => {
      const response = await fetch(
        `http://localhost:8000/api/v1/assignments?page=${page}&page_size=${pageSize}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    }
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Assignments (Page {page} of {data.pages})</h1>

      <ul>
        {data.items.map(assignment => (
          <li key={assignment.id}>
            {assignment.person.name}: {assignment.activity_name}
          </li>
        ))}
      </ul>

      <div>
        <button
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>

        <span> Page {page} of {data.pages} </span>

        <button
          disabled={page === data.pages}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>

      <div>
        Total: {data.total} assignments
      </div>
    </div>
  );
}
```

---

***REMOVED******REMOVED******REMOVED*** 4. Infinite Scroll with Cursor

While the API uses offset-based pagination, you can implement infinite scroll:

**React Example**:

```javascript
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';

function InfiniteAssignmentList() {
  const pageSize = 50;
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['assignments-infinite'],
    queryFn: async ({ pageParam = 1 }) => {
      const response = await fetch(
        `http://localhost:8000/api/v1/assignments?page=${pageParam}&page_size=${pageSize}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    },
    getNextPageParam: (lastPage) => {
      return lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined;
    },
  });

  // Load next page when sentinel is in view
  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, fetchNextPage, hasNextPage]);

  return (
    <div>
      <h1>Assignments (Infinite Scroll)</h1>

      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.items.map(assignment => (
            <div key={assignment.id}>
              {assignment.person.name}: {assignment.activity_name}
            </div>
          ))}
        </div>
      ))}

      {/* Sentinel element */}
      <div ref={ref}>
        {isFetchingNextPage && <div>Loading more...</div>}
      </div>

      {!hasNextPage && <div>No more results</div>}
    </div>
  );
}
```

---

***REMOVED******REMOVED******REMOVED*** 5. Combining Pagination with Filtering

**Python Example**:

```python
def get_filtered_assignments(token, filters, page=1, page_size=100):
    """Get assignments with filters and pagination."""
    params = {
        "page": page,
        "page_size": page_size,
        **filters  ***REMOVED*** Add filter parameters
    }

    response = requests.get(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    return response.json()

***REMOVED*** Usage: Get call assignments for specific date range
filters = {
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "activity_type": "on_call"
}

page1 = get_filtered_assignments(token, filters, page=1)
print(f"Found {page1['total']} call assignments")
```

---

***REMOVED******REMOVED*** Performance Considerations

***REMOVED******REMOVED******REMOVED*** 1. Choose Appropriate Page Size

| Page Size | Use Case | Pros | Cons |
|-----------|----------|------|------|
| 10-20 | Mobile apps, real-time updates | Fast response, low memory | Many requests for large datasets |
| 50-100 | Web dashboards, desktop apps | Balanced | Moderate memory usage |
| 200-500 | Data export, batch processing | Fewer requests | Slower response, higher memory |

***REMOVED******REMOVED******REMOVED*** 2. Caching Strategies

**Cache pages locally**:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=10)
def get_assignments_page(token, page, page_size, cache_key):
    """Cache recent pages for 5 minutes."""
    response = requests.get(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": page, "page_size": page_size}
    )
    return response.json()

***REMOVED*** Cache key includes timestamp rounded to 5 minutes
cache_key = int(time.time() // 300)
data = get_assignments_page(token, page=1, page_size=100, cache_key=cache_key)
```

***REMOVED******REMOVED******REMOVED*** 3. Pre-fetching Next Page

**React Example**:

```javascript
const { data: currentData } = useQuery(['assignments', page]);

// Pre-fetch next page
const { data: nextData } = useQuery(
  ['assignments', page + 1],
  fetchAssignmentsPage,
  {
    enabled: page < currentData?.pages, // Only if next page exists
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  }
);
```

---

***REMOVED******REMOVED*** Validation and Error Handling

***REMOVED******REMOVED******REMOVED*** Invalid Page Number

**Request**:
```bash
curl "http://localhost:8000/api/v1/assignments?page=0&page_size=100"
```

**Response** (422):
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

***REMOVED******REMOVED******REMOVED*** Page Size Too Large

**Request**:
```bash
curl "http://localhost:8000/api/v1/assignments?page=1&page_size=1000"
```

**Response** (422):
```json
{
  "detail": [
    {
      "loc": ["query", "page_size"],
      "msg": "ensure this value is less than or equal to 500",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

***REMOVED******REMOVED******REMOVED*** Page Beyond Total Pages

**Request**:
```bash
curl "http://localhost:8000/api/v1/assignments?page=999&page_size=100"
```

**Response** (200):
```json
{
  "items": [],
  "total": 248,
  "page": 999,
  "page_size": 100,
  "pages": 3
}
```

**Note**: Requesting a page beyond total pages returns empty items array but is not an error.

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Always Specify page_size

```python
***REMOVED*** Good - explicit page size
response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": 1, "page_size": 50}
)

***REMOVED*** Okay - uses default (100)
response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": 1}
)
```

***REMOVED******REMOVED******REMOVED*** 2. Check Total Before Iterating

```python
***REMOVED*** Check if there are any results
response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": 1, "page_size": 1}
)

total = response.json()['total']
if total == 0:
    print("No assignments found")
else:
    print(f"Found {total} assignments, proceeding...")
    ***REMOVED*** Iterate through all pages
```

***REMOVED******REMOVED******REMOVED*** 3. Use Appropriate Page Size for Use Case

```python
***REMOVED*** For UI display (fast, interactive)
ui_params = {"page": 1, "page_size": 20}

***REMOVED*** For data export (fewer requests)
export_params = {"page": 1, "page_size": 500}

***REMOVED*** For real-time monitoring (lightweight)
monitoring_params = {"page": 1, "page_size": 10}
```

***REMOVED******REMOVED******REMOVED*** 4. Handle Empty Results

```python
data = response.json()

if not data['items']:
    if data['page'] > data['pages']:
        print("Page number exceeds total pages")
    else:
        print("No items found")
else:
    process_items(data['items'])
```

---

***REMOVED******REMOVED*** Common Pagination Recipes

***REMOVED******REMOVED******REMOVED*** Get Total Count Without Fetching All Items

```python
***REMOVED*** Fetch just first page with page_size=1 to get total
response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": 1, "page_size": 1}
)

total = response.json()['total']
print(f"Total assignments: {total}")
```

***REMOVED******REMOVED******REMOVED*** Get Last Page

```python
***REMOVED*** Get first page to determine total pages
first_page = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": 1, "page_size": 100}
).json()

***REMOVED*** Fetch last page
last_page = requests.get(
    "http://localhost:8000/api/v1/assignments",
    params={"page": first_page['pages'], "page_size": 100}
).json()

print(f"Last {len(last_page['items'])} assignments:")
for assignment in last_page['items']:
    print(f"  - {assignment['person']['name']}")
```

***REMOVED******REMOVED******REMOVED*** Batch Process with Progress

```python
from tqdm import tqdm

def process_all_assignments(token, batch_size=100):
    """Process all assignments with progress bar."""
    ***REMOVED*** Get total
    first_response = requests.get(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 1}
    ).json()

    total_pages = first_response['pages']

    ***REMOVED*** Process with progress bar
    with tqdm(total=total_pages, desc="Processing assignments") as pbar:
        for page in range(1, total_pages + 1):
            response = requests.get(
                "http://localhost:8000/api/v1/assignments",
                headers={"Authorization": f"Bearer {token}"},
                params={"page": page, "page_size": batch_size}
            ).json()

            ***REMOVED*** Process batch
            process_batch(response['items'])

            pbar.update(1)

***REMOVED*** Usage
process_all_assignments(token, batch_size=100)
```

---

***REMOVED******REMOVED*** See Also

- [Assignments API](endpoints/assignments.md) - Assignment pagination
- [Swaps API](endpoints/swaps.md) - Swap history pagination
- [Resilience API](endpoints/resilience.md) - Health check history pagination
- [Error Codes](error-codes.md) - Pagination error handling
