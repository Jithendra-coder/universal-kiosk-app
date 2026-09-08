from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import KioskPublishRequest, KioskSetupAttestationCreate, KioskSetupUpdate, KioskTestOrderCreate
from services import kiosk_service, setup_service, test_session_service


router = APIRouter(prefix="/businesses/{business_id}/setup", tags=["kiosk-setup"])


@router.get("")
def get_setup(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return setup_service.setup_overview(client, business_id, user_id)


@router.patch("")
def patch_setup(payload: KioskSetupUpdate, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return setup_service.update_setup(client, business_id, user_id, payload)


@router.post("/preview-attestations")
def preview_attestation(payload: KioskSetupAttestationCreate, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return setup_service.attest_preview(client, business_id, user_id, payload.event_version)


@router.post("/test-orders")
def test_order(payload: KioskTestOrderCreate, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return setup_service.create_test_order(client, business_id, user_id, payload)


@router.get("/draft-menu")
def draft_menu(business_id: UUID, location_id: UUID | None = None, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    business = setup_service.assert_workspace_access(client, business_id, user_id)
    return kiosk_service.get_kiosk_payload(client, business["slug"], use_draft=True, location_id=str(location_id) if location_id else None)


@router.post("/test-sessions")
def create_test_session(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"session": test_session_service.create(client, business_id, user_id)}


@router.get("/test-sessions")
def current_test_session(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"session": test_session_service.current(client, business_id, user_id)}


@router.post("/test-sessions/reset")
def reset_test_session(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"session": test_session_service.reset(client, business_id, user_id)}


@router.delete("/test-sessions")
def end_test_session(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    test_session_service.end_current(client, business_id, user_id)
    return {"status": "ended"}


@router.post("/publish")
def publish(payload: KioskPublishRequest, business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return setup_service.publish(client, business_id, user_id, payload.expected_revision, payload.allow_untested)
