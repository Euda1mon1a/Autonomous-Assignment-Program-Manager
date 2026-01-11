# API Patterns

## Overview

This document covers common API usage patterns for the Residency Scheduler. These patterns ensure consistency, type safety, and proper error handling across the application.

## API Type Naming Convention

### The Critical Rule

| Layer | Convention | Example |
|-------|------------|---------|
| Backend (Python) | snake_case | `pgy_level`, `created_at` |
| Frontend (TypeScript) | camelCase | `pgyLevel`, `createdAt` |
| API Wire Format | snake_case | `{"pgy_level": 1}` |

### Automatic Conversion

The axios client in `frontend/src/lib/api.ts` automatically converts:
- **Response:** snake_case → camelCase (for frontend use)
- **Request:** camelCase → snake_case (for API)

### Common Bug Pattern

```typescript
// ❌ WRONG - Will cause runtime undefined errors
interface Person {
  pgy_level: number;      // TypeScript thinks this exists
  created_at: string;
}

// At runtime:
const person = await api.get('/people/1');
console.log(person.pgy_level);  // undefined! Axios converted to pgyLevel
```

```typescript
// ✓ CORRECT
interface Person {
  pgyLevel: number;       // Matches what axios returns
  createdAt: string;
}

// At runtime:
const person = await api.get('/people/1');
console.log(person.pgyLevel);  // Works!
```

### Why TypeScript Doesn't Catch This

TypeScript types are erased at runtime. If your interface says `pgy_level` but axios returns `pgyLevel`, the code will access `undefined` without any compile-time error.

## Backend API Patterns

### Creating an Endpoint

```python
# backend/app/api/routes/people.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/people", tags=["people"])

@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PersonResponse:
    person = await person_service.get(db, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    return PersonResponse.model_validate(person)
```

### Pydantic Schemas

```python
# backend/app/schemas/person.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    pgy_level: int = Field(..., ge=1, le=7)
    is_active: bool = True

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: str | None = None
    pgy_level: int | None = Field(None, ge=1, le=7)
    is_active: bool | None = None

class PersonResponse(PersonBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Service Layer Pattern

```python
# backend/app/services/person_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class PersonService:
    async def get(self, db: AsyncSession, person_id: UUID) -> Person | None:
        result = await db.execute(
            select(Person).where(Person.id == person_id)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, data: PersonCreate) -> Person:
        person = Person(**data.model_dump())
        db.add(person)
        await db.commit()
        await db.refresh(person)
        return person

    async def list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> list[Person]:
        result = await db.execute(
            select(Person)
            .offset(skip)
            .limit(limit)
            .order_by(Person.created_at.desc())
        )
        return list(result.scalars().all())

person_service = PersonService()
```

## Frontend API Patterns

### API Client Setup

```typescript
// frontend/src/lib/api.ts
import axios from 'axios';
import { snakeToCamel, camelToSnake } from './utils';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,
});

// Response interceptor: snake_case → camelCase
api.interceptors.response.use((response) => {
  response.data = snakeToCamel(response.data);
  return response;
});

// Request interceptor: camelCase → snake_case
api.interceptors.request.use((config) => {
  if (config.data) {
    config.data = camelToSnake(config.data);
  }
  return config;
});

export default api;
```

### TanStack Query Usage

```typescript
// frontend/src/features/people/hooks/usePeople.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface Person {
  id: string;
  name: string;
  pgyLevel: number;  // camelCase!
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export function usePeople() {
  return useQuery({
    queryKey: ['people'],
    queryFn: async () => {
      const response = await api.get<Person[]>('/people');
      return response.data;
    },
  });
}

export function useCreatePerson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { name: string; pgyLevel: number }) => {
      const response = await api.post<Person>('/people', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] });
    },
  });
}
```

## Error Handling

### Backend Error Responses

```python
# Structured error format
{
    "detail": "Person not found",
    "code": "NOT_FOUND",
    "field": null
}

# Validation errors (422)
{
    "detail": [
        {
            "loc": ["body", "pgy_level"],
            "msg": "ensure this value is greater than or equal to 1",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

### Frontend Error Handling

```typescript
try {
  await api.post('/people', newPerson);
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 422) {
      // Validation error
      const validationErrors = error.response.data.detail;
      // Handle field-specific errors
    } else if (error.response?.status === 401) {
      // Redirect to login
    } else {
      // Generic error handling
      toast.error(error.response?.data?.detail || 'An error occurred');
    }
  }
}
```

## Authentication Pattern

### Cookie-Based JWT

- Backend sets httpOnly cookie on login
- Frontend automatically sends cookie (withCredentials: true)
- No token storage in localStorage (XSS protection)

```python
# Backend: Set cookie on login
response.set_cookie(
    key="access_token",
    value=f"Bearer {token}",
    httponly=True,
    secure=True,  # HTTPS only in production
    samesite="lax",
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
)
```

### Protected Routes

```typescript
// Frontend: Redirect if not authenticated
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useRouter } from 'next/navigation';

export function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) return <LoadingSpinner />;
  if (!user) return null;

  return children;
}
```

## Pagination Pattern

### Backend

```python
@router.get("/", response_model=PaginatedResponse[PersonResponse])
async def list_people(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total = await person_service.count(db)
    items = await person_service.list(db, skip=skip, limit=limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Frontend

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

function usePaginatedPeople(page: number, pageSize: number = 20) {
  return useQuery({
    queryKey: ['people', 'paginated', page, pageSize],
    queryFn: async () => {
      const skip = (page - 1) * pageSize;
      const response = await api.get<PaginatedResponse<Person>>(
        `/people?skip=${skip}&limit=${pageSize}`
      );
      return response.data;
    },
  });
}
```

## Common HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input format |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Validation Error | Pydantic validation failed |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | Unexpected error |

## Testing API Endpoints

### Backend Tests

```python
@pytest.mark.asyncio
async def test_create_person(client: AsyncClient, db: AsyncSession):
    response = await client.post(
        "/api/v1/people",
        json={"name": "Test Person", "pgy_level": 2}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Person"
    assert data["pgy_level"] == 2
```

### Frontend Tests

```typescript
// Mock uses camelCase (post-axios transformation)
const mockPerson = {
  id: '123',
  name: 'Test Person',
  pgyLevel: 2,  // camelCase!
  isActive: true,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};
```
