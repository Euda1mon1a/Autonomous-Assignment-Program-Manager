# API Developer Agent - Prompt Templates

> **Role:** RESTful API design, versioning, documentation, client SDKs
> **Model:** Claude Opus 4.5
> **Mission:** Build well-designed, documented APIs

## 1. API DESIGN TEMPLATE

```
**API:** ${API_NAME}

**ENDPOINTS:**
${ENDPOINTS_SPEC}

**DESIGN PRINCIPLES:**
- RESTful: Resources as nouns, HTTP methods as verbs
- Versioning: /api/v${VERSION}/resource
- Consistency: Standard response format
- Pagination: limit, offset, total_count
- Filtering: Query parameters
- Sorting: sort, order params

**RESPONSE FORMAT:**
\`\`\`json
{
  "success": true,
  "data": {...},
  "errors": null,
  "meta": {
    "timestamp": "ISO8601",
    "version": "v${VERSION}"
  }
}
\`\`\`

**ERROR FORMAT:**
\`\`\`json
{
  "success": false,
  "data": null,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Field required",
      "field": "name"
    }
  ]
}
\`\`\`

Design and document API comprehensively.
```

## 2. ENDPOINT SPECIFICATION TEMPLATE

```
**ENDPOINT:** ${HTTP_METHOD} ${PATH}

**DESCRIPTION:**
${DESCRIPTION}

**PARAMETERS:**
\`\`\`
Query:
  - limit: integer, max 100 (default: 20)
  - offset: integer, default 0
  - sort: ${SORTABLE_FIELDS}

Path:
  - id: string, UUID format

Body (${HTTP_METHOD} methods):
  - field1: string, required
  - field2: number, optional
\`\`\`

**RESPONSE (200):**
\`\`\`json
{
  "data": {...},
  "meta": {
    "total_count": 100,
    "limit": 20,
    "offset": 0
  }
}
\`\`\`

**ERRORS:**
- 400: Bad Request (validation)
- 401: Unauthorized
- 404: Not Found
- 429: Rate Limited
- 500: Server Error

**RATE LIMIT:**
- ${REQUESTS} requests per ${WINDOW} seconds
- Header: X-RateLimit-Remaining

Specify endpoint completely.
```

## 3. PAGINATION TEMPLATE

```
**PAGINATION IMPLEMENTATION**

**DESIGN:**
\`\`\`python
class PaginationParams(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta = Field(...)

class PaginationMeta(BaseModel):
    total_count: int
    limit: int
    offset: int
    total_pages: int
\`\`\`

**ENDPOINT IMPLEMENTATION:**
\`\`\`python
@router.get("/items")
async def list_items(
    db: AsyncSession,
    params: PaginationParams = Depends()
) -> PaginatedResponse[ItemSchema]:
    # Count total
    count_result = await db.execute(select(func.count(Item.id)))
    total = count_result.scalar()

    # Get page
    result = await db.execute(
        select(Item)
        .offset(params.offset)
        .limit(params.limit)
    )
    items = result.scalars().all()

    return PaginatedResponse(
        data=[ItemSchema.from_orm(item) for item in items],
        meta=PaginationMeta(
            total_count=total,
            limit=params.limit,
            offset=params.offset,
            total_pages=(total + params.limit - 1) // params.limit
        )
    )
\`\`\`

Implement pagination consistently.
```

## 4. FILTERING & SORTING TEMPLATE

```
**FILTERING & SORTING**

**FILTER SCHEMA:**
\`\`\`python
class FilterParams(BaseModel):
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None  # Full-text search

class SortParams(BaseModel):
    sort: str = "created_at"  # Field to sort by
    order: Literal["asc", "desc"] = "desc"
\`\`\`

**IMPLEMENTATION:**
\`\`\`python
def apply_filters(query, filters: FilterParams):
    if filters.status:
        query = query.where(Item.status == filters.status)
    if filters.created_after:
        query = query.where(Item.created_at >= filters.created_after)
    if filters.search:
        query = query.where(
            Item.name.ilike(f"%{filters.search}%")
        )
    return query

def apply_sort(query, sort_params: SortParams):
    column = getattr(Item, sort_params.sort)
    if sort_params.order == "desc":
        column = column.desc()
    return query.order_by(column)

@router.get("/items")
async def list_items(
    db: AsyncSession,
    filters: FilterParams = Depends(),
    sort: SortParams = Depends(),
    pagination: PaginationParams = Depends()
):
    query = select(Item)
    query = apply_filters(query, filters)
    query = apply_sort(query, sort)
    # Apply pagination...
\`\`\`

Implement filtering and sorting.
```

## 5. VERSIONING TEMPLATE

```
**API VERSIONING**

**STRATEGY:** URL Versioning (/api/v1, /api/v2)

**ROUTER STRUCTURE:**
\`\`\`python
# backend/app/api/routes/v1/
├── __init__.py
├── items.py
├── schedules.py
└── users.py

# backend/app/api/routes/v2/
├── __init__.py
├── items.py  # New version
└── schedules.py

# backend/app/main.py
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
api_v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

app.include_router(api_v1_router)
app.include_router(api_v2_router)
\`\`\`

**DEPRECATION:**
- Add deprecation header to old endpoints
- Document sunset date in API docs
- Provide migration guide

**BACKWARD COMPATIBILITY:**
- Keep v1 endpoints working
- Support gradual migration
- Clear communication timeline

Implement API versioning.
```

## 6. DOCUMENTATION TEMPLATE

```
**API DOCUMENTATION**

**FORMAT:** OpenAPI 3.0 (Swagger)

**FASTAPI AUTOMATIC DOCUMENTATION:**
\`\`\`python
# FastAPI auto-generates from docstrings
@router.get("/items/{item_id}", tags=["Items"])
async def get_item(
    item_id: str = Path(..., description="Item unique identifier")
) -> ItemSchema:
    """
    Get a specific item by ID.

    - **item_id**: The unique identifier for the item

    Returns:
        ItemSchema: The requested item

    Raises:
        HTTPException: 404 if item not found
    """
    # Implementation
\`\`\`

**SWAGGER UI:**
- Access at: /docs
- Interactive testing
- Try out endpoints

**REDOC:**
- Access at: /redoc
- Alternative documentation view

**POSTMAN COLLECTION:**
- Export from Swagger UI
- Share with developers

Document APIs comprehensively.
```

## 7. CLIENT SDK TEMPLATE

```
**TYPESCRIPT CLIENT SDK**

**STRUCTURE:**
\`\`\`typescript
// sdk/src/client.ts
import { HTTPClient } from './http-client';

export class SchedulerAPI {
  private client: HTTPClient;

  constructor(baseURL: string, apiKey: string) {
    this.client = new HTTPClient(baseURL, apiKey);
  }

  // Items endpoints
  async getItem(itemId: string): Promise<ItemSchema> {
    return this.client.get(\`/items/\${itemId}\`);
  }

  async listItems(options?: ListOptions): Promise<PaginatedResponse<ItemSchema>> {
    return this.client.get('/items', { params: options });
  }

  async createItem(data: CreateItemInput): Promise<ItemSchema> {
    return this.client.post('/items', { body: data });
  }

  async updateItem(itemId: string, data: UpdateItemInput): Promise<ItemSchema> {
    return this.client.patch(\`/items/\${itemId}\`, { body: data });
  }

  async deleteItem(itemId: string): Promise<void> {
    return this.client.delete(\`/items/\${itemId}\`);
  }
}
\`\`\`

**USAGE:**
\`\`\`typescript
const api = new SchedulerAPI('https://api.example.com', process.env.API_KEY);
const items = await api.listItems({ limit: 10 });
\`\`\`

Implement TypeScript client SDK.
```

## 8. STATUS REPORT TEMPLATE

```
**API DEVELOPER STATUS REPORT**

**ENDPOINTS:**
- Created: ${ENDPOINT_COUNT}
- Documented: ${DOCUMENTED_COUNT}%
- Tested: ${TEST_COVERAGE}%

**SPECIFICATION:**
- OpenAPI version: v${VERSION}
- Endpoints documented: ${DOCUMENTED_ENDPOINTS}
- Request/response schemas: ${SCHEMA_COUNT}

**PERFORMANCE:**
- Average response time: ${AVG_TIME}ms
- P95 response time: ${P95_TIME}ms
- Rate limit violations: ${VIOLATIONS}

**ISSUES:**
${ISSUES}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: API Developer*
*Version: 1.0*
