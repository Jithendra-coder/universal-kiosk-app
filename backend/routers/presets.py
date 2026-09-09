from typing import Optional
from fastapi import APIRouter, Query
from services import preset_service

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("")
def get_all_presets():
    return {
        "presets": preset_service.get_all_menu_presets()
    }


@router.get("/{business_type}")
def get_presets_by_type(business_type: str, description: Optional[str] = Query(default=None)):
    return {
        "presets": preset_service.get_menu_presets_for_business_type(business_type, description)
    }
