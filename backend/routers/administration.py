from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Query

from database import DbClient, get_db_client
from deps import _bearer_token, require_user_id
from schemas import AdministrationInvitationCreate, ApiKeyCreate, ApiResponse, BusinessLocationCreate, BusinessLocationUpdate, CustomRoleAssignment, CustomRoleInput, IntegrationInput, InvitationAccept, PaymentLocationAssignmentInput, SecurityPolicyInput, WebhookCreate
from services import administration_closure_service, administration_service
from services import webhook_delivery_service
from services.auth_service import SESSION_COOKIE_NAME, require_recent_auth, session_id_from_access_token

router = APIRouter(prefix="/businesses/{business_id}/administration", tags=["administration"])


def _current_session(session_cookie: str | None, authorization: str | None) -> UUID | None:
    token = session_cookie or _bearer_token(authorization)
    return session_id_from_access_token(token) if token else None


def _require_recent_auth(client: DbClient, business_id: UUID, user_id: UUID, session_cookie: str | None, authorization: str | None) -> None:
    require_recent_auth(client, business_id, user_id, _current_session(session_cookie, authorization))


@router.get("/overview")
def overview(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return administration_service.overview(client, business_id, user_id)


@router.get("/locations")
def locations(business_id: UUID, search: str | None = Query(default=None, max_length=120), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"locations": administration_service.list_locations(client, business_id, user_id, search)}


@router.post("/locations", response_model=ApiResponse)
def create_location(business_id: UUID, payload: BusinessLocationCreate, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Location created.", data=administration_service.create_location(client, business_id, user_id, payload))


@router.patch("/locations/{location_id}", response_model=ApiResponse)
def update_location(business_id: UUID, location_id: UUID, payload: BusinessLocationUpdate, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Location updated.", data=administration_service.update_location(client, business_id, user_id, location_id, payload))


@router.post("/locations/{location_id}/deactivate", response_model=ApiResponse)
def deactivate_location(business_id: UUID, location_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Location deactivated.", data=administration_service.deactivate_location(client, business_id, user_id, location_id))


@router.delete("/locations/{location_id}", response_model=ApiResponse)
def delete_location(business_id: UUID, location_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    administration_service.delete_location(client, business_id, user_id, location_id)
    return ApiResponse(message="Location deleted.")


@router.get("/activity-log")
def activity_log(business_id: UUID, search: str | None = Query(default=None, max_length=120), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return administration_service.activity_log(client, business_id, user_id, search, limit, offset)


@router.get("/payment-location-assignments")
def list_payment_location_assignments(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"assignments": administration_closure_service.payment_assignments(client, business_id, user_id)}


@router.put("/locations/{location_id}/payment-assignment", response_model=ApiResponse)
def save_payment_location_assignment(business_id: UUID, location_id: UUID, payload: PaymentLocationAssignmentInput, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Payment location assignment saved.", data=administration_closure_service.save_payment_assignment(client, business_id, user_id, location_id, payload))


@router.get("/invitations")
def list_invitations(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"invitations": administration_closure_service.invitations(client, business_id, user_id)}


@router.post("/invitations", response_model=ApiResponse)
def create_invitation(business_id: UUID, invitation: AdministrationInvitationCreate, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Invitation created.", data=administration_closure_service.create_invitation(client, business_id, user_id, invitation.email, invitation.role.value, invitation.location_ids, invitation.expires_in_days))


@router.post("/invitations/{invitation_id}/revoke", response_model=ApiResponse)
def revoke_invitation(business_id: UUID, invitation_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    administration_closure_service.revoke_invitation(client, business_id, user_id, invitation_id)
    return ApiResponse(message="Invitation revoked.")


@router.post("/invitations/{invitation_id}/resend", response_model=ApiResponse)
def resend_invitation(business_id: UUID, invitation_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Invitation resent.", data=administration_closure_service.resend_invitation(client, business_id, user_id, invitation_id))


@router.post("/invitations/accept", response_model=ApiResponse)
def accept_invitation(payload: InvitationAccept, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Invitation accepted.", data=administration_closure_service.accept_invitation(client, user_id, payload))


@router.get("/custom-roles")
def list_custom_roles(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"roles": administration_closure_service.custom_roles(client, business_id, user_id)}


@router.post("/custom-roles", response_model=ApiResponse)
def create_custom_role(business_id: UUID, payload: CustomRoleInput, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Custom role created.", data=administration_closure_service.save_custom_role(client, business_id, user_id, payload))


@router.post("/staff/{staff_id}/custom-role", response_model=ApiResponse)
def assign_custom_role(business_id: UUID, staff_id: UUID, payload: CustomRoleAssignment, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Custom role assigned.", data=administration_closure_service.assign_custom_role(client, business_id, user_id, staff_id, payload))


@router.get("/security-policy")
def get_security_policy(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return administration_closure_service.security_policy(client, business_id, user_id)


@router.put("/security-policy", response_model=ApiResponse)
def update_security_policy(business_id: UUID, payload: SecurityPolicyInput, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    return ApiResponse(message="Security policy updated.", data=administration_closure_service.security_policy(client, business_id, user_id, payload))


@router.get("/sessions")
def list_sessions(business_id: UUID, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"sessions": administration_closure_service.sessions(client, business_id, user_id, _current_session(session_cookie, authorization))}


@router.post("/sessions/revoke-others", response_model=ApiResponse)
def revoke_other_sessions(business_id: UUID, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    administration_closure_service.revoke_session(client, business_id, user_id, user_id, all_others=True, current_session_id=_current_session(session_cookie, authorization))
    return ApiResponse(message="Other sessions revoked.")


@router.post("/sessions/{session_id}/revoke", response_model=ApiResponse)
def revoke_session(business_id: UUID, session_id: UUID, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    administration_closure_service.revoke_session(client, business_id, user_id, session_id)
    return ApiResponse(message="Session revoked.")


@router.get("/integrations")
def list_integrations(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"integrations": administration_closure_service.integrations(client, business_id, user_id)}


@router.post("/integrations", response_model=ApiResponse)
def create_integration(business_id: UUID, payload: IntegrationInput, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Integration saved.", data=administration_closure_service.create_integration(client, business_id, user_id, payload))


@router.get("/api-keys")
def list_api_keys(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"api_keys": administration_closure_service.api_keys(client, business_id, user_id)}


@router.post("/api-keys", response_model=ApiResponse)
def create_api_key(business_id: UUID, payload: ApiKeyCreate, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    return ApiResponse(message="Copy this API key now; it will not be shown again.", data=administration_closure_service.create_api_key(client, business_id, user_id, payload))


@router.post("/api-keys/{key_id}/rotate", response_model=ApiResponse)
def rotate_api_key(business_id: UUID, key_id: UUID, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    return ApiResponse(message="API key rotated; copy the new secret now.", data=administration_closure_service.rotate_api_key(client, business_id, user_id, key_id))


@router.post("/api-keys/{key_id}/revoke", response_model=ApiResponse)
def revoke_api_key(business_id: UUID, key_id: UUID, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    administration_closure_service.revoke_api_key(client, business_id, user_id, key_id)
    return ApiResponse(message="API key revoked.")


@router.get("/webhooks")
def list_webhooks(business_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"webhooks": administration_closure_service.webhooks(client, business_id, user_id)}


@router.post("/webhooks", response_model=ApiResponse)
def create_webhook(business_id: UUID, payload: WebhookCreate, authorization: str | None = Header(default=None), session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    _require_recent_auth(client, business_id, user_id, session_cookie, authorization)
    return ApiResponse(message="Copy this signing secret now; it will not be shown again.", data=administration_closure_service.create_webhook(client, business_id, user_id, payload))


@router.post("/webhooks/{webhook_id}/enable", response_model=ApiResponse)
def enable_webhook(business_id: UUID, webhook_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Webhook enabled.", data=administration_closure_service.set_webhook_state(client, business_id, user_id, webhook_id, True))


@router.post("/webhooks/{webhook_id}/disable", response_model=ApiResponse)
def disable_webhook(business_id: UUID, webhook_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Webhook disabled.", data=administration_closure_service.set_webhook_state(client, business_id, user_id, webhook_id, False))


@router.delete("/webhooks/{webhook_id}", response_model=ApiResponse)
def delete_webhook(business_id: UUID, webhook_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    administration_closure_service.delete_webhook(client, business_id, user_id, webhook_id)
    return ApiResponse(message="Webhook deleted.")


@router.get("/webhooks/{webhook_id}/deliveries")
def list_webhook_deliveries(business_id: UUID, webhook_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"deliveries": administration_closure_service.webhook_deliveries(client, business_id, user_id, webhook_id)}


@router.post("/webhooks/{webhook_id}/deliveries/{delivery_id}/retry", response_model=ApiResponse)
def retry_webhook_delivery(business_id: UUID, webhook_id: UUID, delivery_id: UUID, user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return ApiResponse(message="Webhook retry queued.", data=webhook_delivery_service.retry_delivery(client, business_id, user_id, delivery_id))


@router.get("/integration-activity")
def integration_activity(business_id: UUID, limit: int = Query(default=50, ge=1, le=100), user_id: UUID = Depends(require_user_id), client: DbClient = Depends(get_db_client)):
    return {"events": administration_closure_service.integration_activity(client, business_id, user_id, limit)}
