from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import ApiResponse
from services.business_service import ADMIN_ROLES, assert_business_access
from services.storage_service import upload_asset
from services.rate_limit_service import RateLimitRule, assert_rate_limit

router = APIRouter(tags=["uploads"])
UPLOAD_LIMIT = RateLimitRule("upload:asset", 20, 60)


@router.post("/businesses/{business_id}/uploads/product-image", response_model=ApiResponse)
async def upload_product_image(
    business_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ADMIN_ROLES)
    assert_rate_limit(request, UPLOAD_LIMIT, identity_parts=[str(user_id), str(business_id), "product"])
    result = await upload_asset(
        business_id,
        file,
        folder="products",
    )
    return ApiResponse(message="Product image uploaded.", data=result)


@router.post("/businesses/{business_id}/uploads/brand-asset", response_model=ApiResponse)
async def upload_brand_asset(
    business_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ADMIN_ROLES)
    assert_rate_limit(request, UPLOAD_LIMIT, identity_parts=[str(user_id), str(business_id), "brand"])
    result = await upload_asset(
        business_id,
        file,
        folder="brand",
    )
    return ApiResponse(message="Brand asset uploaded.", data=result)
