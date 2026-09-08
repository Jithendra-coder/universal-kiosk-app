"""Preview kiosk sandbox routes.

This file is preview sandbox only. It must not call real kiosk/order/payment/PIN/kitchen/cache APIs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas_preview_kiosk import PreviewKioskRenderRequest
from services import preview_kiosk_service

router = APIRouter(prefix="/admin/preview-kiosk", tags=["admin-preview-kiosk"])


@router.post("/render")
def render_preview_kiosk(
    payload: PreviewKioskRenderRequest,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    preview = preview_kiosk_service.render_preview_kiosk(client, user_id, payload)
    return {"preview": preview}
