from fastapi import APIRouter

from app.models import SearchRequest, SearchResponse
from app.services.cache import search_cache
from app.services.supplier_search import find_suppliers

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    cache_key = search_cache.make_key(req.category, req.region, req.keywords, str(req.limit))
    cached = search_cache.get(cache_key)
    if cached is not None:
        suppliers, used_ai, warning = cached
        return SearchResponse(query=req, suppliers=suppliers, used_ai=used_ai, cached=True, warning=warning)

    suppliers, used_ai, warning = await find_suppliers(req)
    search_cache.set(cache_key, (suppliers, used_ai, warning))
    return SearchResponse(query=req, suppliers=suppliers, used_ai=used_ai, cached=False, warning=warning)
