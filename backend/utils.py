import re
from datetime import datetime, timezone
from typing import Any, Dict


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def clean_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "business"


def timestamps_for_status(status: str) -> Dict[str, Any]:
    current = now_utc().isoformat()
    if status == "preparing":
        return {"prep_started_at": current}
    if status == "ready":
        return {"ready_at": current}
    if status == "completed":
        return {"completed_at": current}
    if status == "cancelled":
        return {"cancelled_at": current}
    return {}
