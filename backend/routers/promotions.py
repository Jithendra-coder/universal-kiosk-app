from uuid import UUID

from fastapi import APIRouter, Depends, Response

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import PromotionCreate, PromotionUpdate
from services import promotion_service

router = APIRouter(prefix="/businesses/{business_id}/promotions", tags=["promotions"])

@router.get("")
def list_promotions(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return promotion_service.list_promotions(client, business_id, user_id)

@router.post("")
def create_promotion(payload: PromotionCreate, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return promotion_service.create_promotion(client, business_id, user_id, payload)

@router.patch("/{promotion_id}")
def update_promotion(payload: PromotionUpdate, promotion_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return promotion_service.update_promotion(client, promotion_id, user_id, payload)

@router.delete("/{promotion_id}", status_code=204)
def delete_promotion(promotion_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    promotion_service.delete_promotion(client, promotion_id, user_id)
    return Response(status_code=204)
