from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import AlertStatusUpdate, ApiResponse
from services import alert_service

router = APIRouter(tags=["alerts"])


@router.get("/businesses/{business_id}/alerts")
def list_alerts(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return alert_service.list_alerts(client, business_id, user_id)


@router.get("/businesses/{business_id}/alerts/summary")
def alert_summary(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return alert_service.alert_summary(client, business_id, user_id)


@router.patch("/alerts/{alert_id}", response_model=ApiResponse)
def update_alert(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    alert = alert_service.update_alert_status(client, alert_id, user_id, payload)
    return ApiResponse(message="Alert updated.", data=alert)
