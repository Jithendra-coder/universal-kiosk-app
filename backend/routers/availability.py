from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import ApiResponse, AvailabilityRuleCreate, AvailabilityRuleUpdate
from services import availability_service


router = APIRouter(prefix="/businesses/{business_id}/availability", tags=["availability"])


@router.get("")
def get_availability(business_id: UUID, location_id: UUID | None = None, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return availability_service.overview(client, business_id, user_id, location_id)


@router.post("/rules", response_model=ApiResponse)
def create_rule(business_id: UUID, payload: AvailabilityRuleCreate, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Availability rule created.", data=availability_service.create_rule(client, business_id, user_id, payload))


@router.patch("/rules/{rule_id}", response_model=ApiResponse)
def update_rule(business_id: UUID, rule_id: UUID, payload: AvailabilityRuleUpdate, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Availability rule updated.", data=availability_service.update_rule(client, business_id, rule_id, user_id, payload))


@router.delete("/rules/{rule_id}", response_model=ApiResponse)
def delete_rule(business_id: UUID, rule_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    availability_service.delete_rule(client, business_id, rule_id, user_id)
    return ApiResponse(message="Availability rule deleted.")
