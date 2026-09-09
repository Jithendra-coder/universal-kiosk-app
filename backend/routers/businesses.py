from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import ApiResponse, BusinessCreate, BusinessTypeSelection, BusinessUpdate, OnboardingStatus, OwnerPinSet, StaffInvite, StaffUpdate
from services import business_service, capability_service, pin_service, schedule_service, staff_service

router = APIRouter(prefix="/businesses", tags=["businesses"])
onboarding_router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@onboarding_router.get("/status", response_model=OnboardingStatus)
def get_onboarding_status(
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return business_service.onboarding_status(client, user_id)


@onboarding_router.get("/business-type")
def get_onboarding_business_type(
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return business_service.get_onboarding_business_type(client, user_id)


@onboarding_router.put("/business-type")
def set_onboarding_business_type(
    payload: BusinessTypeSelection,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return business_service.set_onboarding_business_type(
        client,
        user_id,
        payload.business_type.value,
        payload.business_description,
    )


@router.get("/me")
def get_my_business(
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.get_primary_business_for_user(client, user_id)
    role = business_service.get_business_role_for_user(client, business, user_id).value if business else None
    return {"business": business_service.serialize_business_for_response(business), "role": role}


@router.post("", response_model=ApiResponse)
def create_business(
    payload: BusinessCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.create_business(client, user_id, payload)
    return ApiResponse(message="Business created.", data=business_service.serialize_business_for_response(business))


@router.get("/slug-options")
def get_slug_options(
    name: str | None = None,
    slug: str | None = None,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return business_service.slug_options(client, user_id, name=name, slug=slug)


@router.get("/capabilities/{business_type}")
def get_business_capabilities(business_type: str):
    return {
        "capabilities": capability_service.get_capabilities(business_type),
        "itemTypeOptions": capability_service.get_item_type_options(business_type),
    }


@router.get("/{business_id}/operating-status")
def get_business_operating_status(
    business_id: UUID,
    client: DbClient = Depends(get_db_client),
):
    business = business_service.get_business_by_id(client, business_id)
    return schedule_service.get_store_availability(business)


@router.get("/{business_id}")
def get_business(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.assert_business_access(client, business_id, user_id)
    return {"business": business_service.serialize_business_for_response(business)}


@router.patch("/{business_id}", response_model=ApiResponse)
def update_business(
    business_id: UUID,
    payload: BusinessUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.update_business(client, business_id, user_id, payload)
    return ApiResponse(message="Business updated.", data=business_service.serialize_business_for_response(business))


@router.get("/{business_id}/settings")
def get_business_settings(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.assert_business_access(client, business_id, user_id, business_service.ADMIN_ROLES)
    return {"settings": business_service.serialize_business_for_response(business)}


@router.patch("/{business_id}/settings", response_model=ApiResponse)
def update_business_settings(
    business_id: UUID,
    payload: BusinessUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    business = business_service.update_business(client, business_id, user_id, payload)
    return ApiResponse(message="Settings updated.", data=business_service.serialize_business_for_response(business))


@router.post("/{business_id}/owner-pin", response_model=ApiResponse)
def set_owner_pin(
    business_id: UUID,
    payload: OwnerPinSet,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    result = pin_service.set_owner_pin(client, business_id, user_id, payload)
    return ApiResponse(message="Owner PIN updated.", data=result)


@router.get("/{business_id}/staff")
def list_staff(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return {"staff": staff_service.list_staff(client, business_id, user_id)}


@router.post("/{business_id}/staff", response_model=ApiResponse)
def invite_staff(
    business_id: UUID,
    payload: StaffInvite,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    staff = staff_service.invite_staff(client, business_id, user_id, payload)
    return ApiResponse(message="Staff access email sent.", data=staff)


@router.delete("/{business_id}/staff/{staff_id}", response_model=ApiResponse)
def remove_staff(
    business_id: UUID,
    staff_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    staff_service.remove_staff(client, business_id, user_id, staff_id)
    return ApiResponse(message="Staff access removed.")


@router.patch("/{business_id}/staff/{staff_id}", response_model=ApiResponse)
def update_staff(
    business_id: UUID,
    staff_id: UUID,
    payload: StaffUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    staff = staff_service.update_staff(client, business_id, user_id, staff_id, payload)
    return ApiResponse(message="Staff access updated.", data=staff)
