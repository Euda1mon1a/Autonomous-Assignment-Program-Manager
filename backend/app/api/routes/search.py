"""Search API routes.

Provides endpoints for:
- Full-text search across entities
- Autocomplete suggestions
- Specialized search endpoints (people, rotations, procedures)
- Quick search
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.search import (
    PeopleSearchRequest,
    ProcedureSearchRequest,
    QuickSearchResponse,
    RotationSearchRequest,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SuggestionRequest,
    SuggestionResponse,
)
from app.services.search.indexer import SearchService

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Execute a search query across specified entity types.

    Features:
    - Full-text search with relevance ranking
    - Fuzzy matching for typo tolerance
    - Faceted search for filtering
    - Result highlighting
    - Pagination

    Requires authentication.
    """
    try:
        service = SearchService(db)
        results = await service.search(
            query_string=request.query,
            entity_types=request.entity_types,
            filters=request.filters,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )

        return SearchResponse(
            items=[SearchResultItem(**item) for item in results["items"]],
            total=results["total"],
            page=results["page"],
            page_size=results["page_size"],
            total_pages=results["total_pages"],
            facets=results.get("facets", {}),
            query=results["query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/quick", response_model=QuickSearchResponse)
async def quick_search(
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    entity_type: str = Query(default="person", description="Entity type to search"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Quick search endpoint with minimal parameters.

    Useful for search-as-you-type functionality.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        indexer = service.indexer
        items = await indexer.quick_search(
            query_string=query,
            entity_type=entity_type,
            limit=limit,
        )

        return QuickSearchResponse(
            items=[SearchResultItem(**item) for item in items],
            query=query,
            entity_type=entity_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Quick search failed")


@router.post("/people", response_model=SearchResponse)
async def search_people(
    request: PeopleSearchRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for people (residents and faculty).

    Supports filtering by:
    - Person type (resident/faculty)
    - PGY level (for residents)
    - Faculty role

    Requires authentication.
    """
    try:
        service = SearchService(db)
        results = await service.search_people(
            query_string=request.query,
            person_type=request.type,
            pgy_level=request.pgy_level,
            page=request.page,
            page_size=request.page_size,
        )

        return SearchResponse(
            items=[SearchResultItem(**item) for item in results["items"]],
            total=results["total"],
            page=results["page"],
            page_size=results["page_size"],
            total_pages=results["total_pages"],
            facets=results.get("facets", {}),
            query=results["query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="People search failed")


@router.post("/rotations", response_model=SearchResponse)
async def search_rotations(
    request: RotationSearchRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for rotation templates.

    Supports filtering by category.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        indexer = service.indexer
        results = await indexer.search_rotations(
            query_string=request.query,
            category=request.category,
            page=request.page,
            page_size=request.page_size,
        )

        return SearchResponse(
            items=[SearchResultItem(**item) for item in results["items"]],
            total=results["total"],
            page=results["page"],
            page_size=results["page_size"],
            total_pages=results["total_pages"],
            facets=results.get("facets", {}),
            query=results["query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Rotation search failed")


@router.post("/procedures", response_model=SearchResponse)
async def search_procedures(
    request: ProcedureSearchRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for procedures.

    Searches procedure names and CPT codes.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        indexer = service.indexer
        results = await indexer.search_procedures(
            query_string=request.query,
            page=request.page,
            page_size=request.page_size,
        )

        return SearchResponse(
            items=[SearchResultItem(**item) for item in results["items"]],
            total=results["total"],
            page=results["page"],
            page_size=results["page_size"],
            total_pages=results["total_pages"],
            facets=results.get("facets", {}),
            query=results["query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Procedure search failed")


@router.post("/global", response_model=SearchResponse)
async def global_search(
    query: str = Query(..., min_length=1, max_length=500, description="Search query"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search across all entity types.

    Returns results from people, rotations, procedures, assignments, and swaps.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        indexer = service.indexer
        results = await indexer.global_search(
            query_string=query,
            page=page,
            page_size=page_size,
        )

        return SearchResponse(
            items=[SearchResultItem(**item) for item in results["items"]],
            total=results["total"],
            page=results["page"],
            page_size=results["page_size"],
            total_pages=results["total_pages"],
            facets=results.get("facets", {}),
            query=results["query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Global search failed")


@router.post("/suggest", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get autocomplete suggestions for a partial query.

    Useful for search-as-you-type functionality with dropdown suggestions.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        suggestions = await service.suggest(
            query_string=request.query,
            entity_type=request.entity_type,
            limit=request.limit,
        )

        return SuggestionResponse(
            suggestions=suggestions,
            query=request.query,
            entity_type=request.entity_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Suggestion request failed")


@router.get("/suggest", response_model=SuggestionResponse)
async def get_suggestions_get(
    query: str = Query(
        ..., min_length=1, max_length=200, description="Partial search query"
    ),
    entity_type: str = Query(
        default="person", description="Entity type for suggestions"
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum suggestions"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get autocomplete suggestions (GET endpoint).

    Alternative GET endpoint for autocomplete suggestions.
    Requires authentication.
    """
    try:
        service = SearchService(db)
        suggestions = await service.suggest(
            query_string=query,
            entity_type=entity_type,
            limit=limit,
        )

        return SuggestionResponse(
            suggestions=suggestions,
            query=query,
            entity_type=entity_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Suggestion request failed")
