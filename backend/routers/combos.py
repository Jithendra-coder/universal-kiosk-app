from uuid import UUID

from fastapi import APIRouter, Depends

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import (
    ApiResponse,
    ComboCreate,
    ComboOptionCreate,
    ComboOptionUpdate,
    ComboSectionCreate,
    ComboSectionUpdate,
    ComboUpdate,
)
from services import combo_service


router = APIRouter(tags=["admin combos"])


@router.get("/businesses/{business_id}/combos")
def list_combos(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return {"combos": combo_service.list_combos(client, business_id, user_id)}


@router.get("/businesses/{business_id}/combo-items")
def list_combo_items(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return {"products": combo_service.list_selectable_items(client, business_id, user_id)}


@router.post("/businesses/{business_id}/combos", response_model=ApiResponse)
def create_combo(
    business_id: UUID,
    payload: ComboCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo created.",
        data=combo_service.create_combo(client, business_id, user_id, payload),
    )


@router.get("/combos/{combo_id}")
def get_combo(
    combo_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return {"combo": combo_service.get_combo(client, combo_id, user_id)}


@router.patch("/combos/{combo_id}", response_model=ApiResponse)
def update_combo(
    combo_id: UUID,
    payload: ComboUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo updated.",
        data=combo_service.update_combo(client, combo_id, user_id, payload),
    )


@router.delete("/combos/{combo_id}", response_model=ApiResponse)
def delete_combo(
    combo_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    combo_service.delete_combo(client, combo_id, user_id)
    return ApiResponse(message="Combo deleted.")


@router.post("/combos/{combo_id}/duplicate", response_model=ApiResponse)
def duplicate_combo(
    combo_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo duplicated as a draft.",
        data=combo_service.duplicate_combo(client, combo_id, user_id),
    )


@router.post("/combos/{combo_id}/sections", response_model=ApiResponse)
def create_section(
    combo_id: UUID,
    payload: ComboSectionCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo section created.",
        data=combo_service.create_section(client, combo_id, user_id, payload),
    )


@router.patch("/combo-sections/{section_id}", response_model=ApiResponse)
def update_section(
    section_id: UUID,
    payload: ComboSectionUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo section updated.",
        data=combo_service.update_section(client, section_id, user_id, payload),
    )


@router.delete("/combo-sections/{section_id}", response_model=ApiResponse)
def delete_section(
    section_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    combo_service.delete_section(client, section_id, user_id)
    return ApiResponse(message="Combo section deleted.")


@router.post("/combo-sections/{section_id}/options", response_model=ApiResponse)
def create_option(
    section_id: UUID,
    payload: ComboOptionCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo option created.",
        data=combo_service.create_option(client, section_id, user_id, payload),
    )


@router.patch("/combo-options/{option_id}", response_model=ApiResponse)
def update_option(
    option_id: UUID,
    payload: ComboOptionUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return ApiResponse(
        message="Combo option updated.",
        data=combo_service.update_option(client, option_id, user_id, payload),
    )


@router.delete("/combo-options/{option_id}", response_model=ApiResponse)
def delete_option(
    option_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    combo_service.delete_option(client, option_id, user_id)
    return ApiResponse(message="Combo option deleted.")
