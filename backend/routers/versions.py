from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from services import version_service

router = APIRouter(prefix="/businesses/{business_id}/kiosk-versions", tags=["kiosk-versions"])

@router.get("")
def list_versions(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return version_service.list_versions(client, business_id, user_id)

@router.get("/{version_id}/compare")
def compare_version(version_id: UUID, business_id: UUID, against: str = "live", user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    if against not in {"live", "draft"}: from fastapi import HTTPException; raise HTTPException(status_code=400, detail="against must be live or draft")
    return version_service.compare(client, business_id, user_id, version_id, against)

@router.get("/{version_id}/snapshot")
def version_snapshot(version_id: UUID, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return version_service.snapshot(client, business_id, user_id, version_id)

@router.post("/{version_id}/restore")
def restore_version(version_id: UUID, business_id: UUID, expected_revision: int, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return version_service.restore_as_new_draft(client, business_id, user_id, version_id, expected_revision)
