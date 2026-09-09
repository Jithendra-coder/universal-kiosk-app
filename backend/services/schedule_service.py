from datetime import datetime
from typing import Any, Dict, List, Optional
import zoneinfo

STORE_DAY_KEYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def to_minutes(value: str) -> int:
    try:
        parts = value[:5].split(":")
        hour = int(parts[0]) if parts[0].isdigit() else 0
        minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return hour * 60 + minute
    except Exception:
        return 0


def format_clock(value: str) -> str:
    try:
        parts = value[:5].split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        period = "AM" if hour < 12 else "PM"
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"
    except Exception:
        return value


def is_within_slot(minutes: int, slot: Dict[str, Any]) -> bool:
    open_min = to_minutes(slot.get("open", "00:00"))
    close_min = to_minutes(slot.get("close", "00:00"))
    if open_min == close_min:
        return True
    if open_min < close_min:
        return open_min <= minutes < close_min
    return minutes >= open_min or minutes < close_min


def normalize_slots(slots: Optional[List[Dict[str, str]]], opening: str, closing: str) -> List[Dict[str, str]]:
    valid = [s for s in (slots or []) if s.get("open") and s.get("close")]
    return valid if valid else [{"open": opening, "close": closing}]


def normalize_store_schedule(business: Any) -> Dict[str, Any]:
    b_dict = business if isinstance(business, dict) else (business.__dict__ if hasattr(business, "__dict__") else {})
    opening = (b_dict.get("opening_time") or "09:00")[:5]
    closing = (b_dict.get("closing_time") or "22:00")[:5]
    source = b_dict.get("store_schedule") or {}
    if not isinstance(source, dict):
        source = {}

    weekly: Dict[str, Dict[str, Any]] = {}
    source_weekly = source.get("weekly") or {}
    for day in STORE_DAY_KEYS:
        saved = source_weekly.get(day) or {}
        weekly[day] = {
            "closed": bool(saved.get("closed", False)),
            "slots": normalize_slots(saved.get("slots"), opening, closing),
        }

    overrides = []
    for override in source.get("overrides") or []:
        overrides.append({
            **override,
            "slots": normalize_slots(override.get("slots"), opening, closing),
        })

    return {
        "enabled": source.get("enabled", True),
        "weekly": weekly,
        "overrides": overrides,
        "emergency_closed": bool(source.get("emergency_closed", False)),
        "emergency_message": (source.get("emergency_message") or "").strip()
        or "We are temporarily unavailable. Please check back shortly.",
    }


def next_opening_message(schedule: Dict[str, Any], current_day: str) -> str:
    try:
        start = STORE_DAY_KEYS.index(current_day)
    except ValueError:
        start = 0

    for offset in range(1, 8):
        day = STORE_DAY_KEYS[(start + offset) % len(STORE_DAY_KEYS)]
        entry = schedule["weekly"].get(day, {})
        slots = entry.get("slots", [])
        if not entry.get("closed") and slots:
            label = day.capitalize()
            return f"Ordering opens {label} at {format_clock(slots[0]['open'])}."

    return "This location is not accepting new orders right now."


def get_store_availability(business: Any, now: Optional[datetime] = None) -> Dict[str, Any]:
    b_dict = business if isinstance(business, dict) else (business.__dict__ if hasattr(business, "__dict__") else {})

    if not b_dict.get("is_active", True):
        return {
            "isOpen": False,
            "title": "Orders are paused",
            "message": "This location is not accepting new orders right now.",
            "shortMessage": "Not accepting orders",
        }

    schedule = normalize_store_schedule(b_dict)
    if schedule["emergency_closed"]:
        return {
            "isOpen": False,
            "title": "Temporarily unavailable",
            "message": schedule["emergency_message"],
            "shortMessage": "Temporarily unavailable",
        }

    tz_name = b_dict.get("timezone") or "Asia/Kolkata"
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")

    current_dt = now or datetime.now(tz)
    if current_dt.tzinfo is None:
        current_dt = current_dt.replace(tzinfo=tz)
    else:
        current_dt = current_dt.astimezone(tz)

    day_name = STORE_DAY_KEYS[current_dt.weekday()]
    date_str = current_dt.strftime("%Y-%m-%d")
    current_minutes = current_dt.hour * 60 + current_dt.minute

    override = next((entry for entry in schedule["overrides"] if entry.get("date") == date_str), None)
    day_schedule = override or schedule["weekly"].get(day_name, {"closed": False, "slots": []})

    if not schedule["enabled"]:
        opening_time = b_dict.get("opening_time")
        closing_time = b_dict.get("closing_time")
        if not opening_time or not closing_time:
            return {"isOpen": True, "title": "Open now", "message": "Ready for orders.", "shortMessage": "Ready for orders"}
        slot = {"open": str(opening_time)[:5], "close": str(closing_time)[:5]}
        if is_within_slot(current_minutes, slot):
            return {
                "isOpen": True,
                "title": "Open now",
                "message": f"Open until {format_clock(slot['close'])}.",
                "shortMessage": f"Open until {format_clock(slot['close'])}",
            }
        return {
            "isOpen": False,
            "title": "Store closed",
            "message": f"Ordering opens at {format_clock(slot['open'])}.",
            "shortMessage": f"Opens at {format_clock(slot['open'])}",
        }

    if day_schedule.get("closed") or not day_schedule.get("slots"):
        override_label = override.get("label") if override else None
        return {
            "isOpen": False,
            "title": f"{override_label}: closed" if override_label else "Store closed",
            "message": next_opening_message(schedule, day_name),
            "shortMessage": "Closed today",
        }

    active_slot = next((s for s in day_schedule["slots"] if is_within_slot(current_minutes, s)), None)
    if active_slot:
        return {
            "isOpen": True,
            "title": "Open now",
            "message": f"Open until {format_clock(active_slot['close'])}.",
            "shortMessage": f"Open until {format_clock(active_slot['close'])}",
        }

    next_today = next((s for s in day_schedule["slots"] if current_minutes < to_minutes(s["open"])), None)
    if next_today:
        return {
            "isOpen": False,
            "title": "Store closed",
            "message": f"Ordering opens today at {format_clock(next_today['open'])}.",
            "shortMessage": f"Opens at {format_clock(next_today['open'])}",
        }

    return {
        "isOpen": False,
        "title": "Store closed",
        "message": next_opening_message(schedule, day_name),
        "shortMessage": "Closed",
    }
