from fastapi import APIRouter, Depends, Query, Request

from deps import require_user_id
from services import pexels_service
from services.rate_limit_service import RateLimitRule, assert_rate_limit

router = APIRouter(tags=["media"])
PEXELS_SEARCH_LIMIT = RateLimitRule("media:pexels-search", 30, 60)


@router.get("/media/pexels/search")
def search_pexels_images(
    request: Request,
    q: str = Query(..., min_length=2, max_length=120),
    per_page: int = Query(12, ge=1, le=24),
    user_id=Depends(require_user_id),
):
    assert_rate_limit(request, PEXELS_SEARCH_LIMIT, identity_parts=[str(user_id)])
    return pexels_service.search_photos(q, per_page)
