from uuid import UUID

from fastapi import APIRouter, Depends
from datetime import datetime

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import ApiResponse, OrderStatusUpdate
from services import order_service
from services.business_service import ORDER_VIEW_ROLES, assert_business_access

router = APIRouter(tags=["orders"])


@router.get("/businesses/{business_id}/orders")
def list_orders(
    business_id: UUID,
    status: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    location_id: UUID | None = None,
    limit: int = 100,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ORDER_VIEW_ROLES)
    return {"orders": order_service.list_orders(client, business_id, status_filter=status, start=start, end=end, location_id=location_id, limit=limit)}


@router.get("/businesses/{business_id}/orders/active")
def list_active_orders(
    business_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    location_id: UUID | None = None,
    limit: int = 100,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ORDER_VIEW_ROLES)
    return {"orders": order_service.list_orders(client, business_id, status_filter="active", start=start, end=end, location_id=location_id, limit=limit)}


@router.get("/businesses/{business_id}/orders/completed")
def list_completed_orders(
    business_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    location_id: UUID | None = None,
    limit: int = 100,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ORDER_VIEW_ROLES)
    return {"orders": order_service.list_orders(client, business_id, status_filter="completed", start=start, end=end, location_id=location_id, limit=limit)}


@router.get("/businesses/{business_id}/orders/done")
def list_done_orders(
    business_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    location_id: UUID | None = None,
    limit: int = 100,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, ORDER_VIEW_ROLES)
    return {"orders": order_service.list_orders(client, business_id, status_filter="done", start=start, end=end, location_id=location_id, limit=limit)}


@router.patch("/orders/{order_id}/status", response_model=ApiResponse)
def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    order = order_service.update_order_status(client, user_id, order_id, payload)
    return ApiResponse(message="Order status updated.", data=order)
