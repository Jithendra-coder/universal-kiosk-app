from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from database import DbClient
from services import business_service, setup_service


def list_versions(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    _access(client, business_id, user_id)
    rows = client.fetch_all("select id, version_number, config_signature, snapshot, published_by, published_at, source_draft_id from kiosk_published_versions where business_id = %(id)s order by version_number desc limit 100", {"id": str(business_id)})
    versions = []
    for index, row in enumerate(rows):
        older = rows[index + 1] if index + 1 < len(rows) else None
        domains = _domains(row.get("snapshot") or {}, older.get("snapshot") if older else {}) if older else []
        changed = [domain["label"] for domain in domains if domain["changed"]]
        versions.append({**_metadata(row), "change_count": sum(domain["changed"] for domain in domains), "changed_areas": changed or (["Initial kiosk configuration"] if not older else ["Published configuration"])})
    return {"versions": versions}


def compare(client: DbClient, business_id: UUID, user_id: UUID, version_id: UUID, against: str = "live") -> dict:
    business = _access(client, business_id, user_id)
    version = _version(client, business_id, version_id)
    if against == "draft": current = setup_service.canonical_configuration(client, business)[1]
    else: current = setup_service.live_configuration(client, business)
    return {"version": _metadata(version), "against": against, "domains": _domains(version["snapshot"], current)}


def snapshot(client: DbClient, business_id: UUID, user_id: UUID, version_id: UUID) -> dict:
    _access(client, business_id, user_id)
    version = _version(client, business_id, version_id)
    return {"version": _metadata(version), "snapshot": version["snapshot"]}


def restore_as_new_draft(client: DbClient, business_id: UUID, user_id: UUID, version_id: UUID, expected_revision: int) -> dict:
    _access(client, business_id, user_id)
    business = client.fetch_one("select * from businesses where id=%(id)s for update", {"id": str(business_id)})
    if not business: raise HTTPException(status_code=404, detail="Business not found.")
    version = _version(client, business_id, version_id)
    setup = dict((business.get("kiosk_order_settings") or {}).get("setup") or {})
    if int(setup.get("revision") or 0) != expected_revision: raise HTTPException(status_code=409, detail="The kiosk draft changed in another session.")
    draft_id = uuid4()
    lineage = client.fetch_one("insert into kiosk_restore_lineage (business_id, source_version_id, draft_id, created_by) values (%(business_id)s, %(source_version_id)s, %(draft_id)s, %(user_id)s) returning *", {"business_id": str(business_id), "source_version_id": str(version_id), "draft_id": str(draft_id), "user_id": str(user_id)})
    setup.update({"draftId": str(draft_id), "restoredSnapshot": version["snapshot"], "revision": expected_revision + 1, "currentStep": "review-publish", "active": True})
    client.fetch_one("update businesses set kiosk_order_settings = %(settings)s where id = %(business_id)s returning id", {"business_id": str(business_id), "settings": Jsonb({**(business.get("kiosk_order_settings") or {}), "setup": setup})})
    client.table("audit_logs").insert({"business_id": str(business_id), "user_id": str(user_id), "action": "kiosk_version_restored_as_draft", "entity": "kiosk_published_version", "entity_id": str(version_id), "metadata": Jsonb({"draft_id": str(draft_id)})}).execute()
    return {"draft_id": str(draft_id), "source_version_id": str(version_id), "lineage": lineage, "setup": setup}


def _access(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    return business_service.assert_business_access(client, business_id, user_id, business_service.FULL_ACCESS_ROLES)


def _version(client: DbClient, business_id: UUID, version_id: UUID) -> dict:
    row = client.fetch_one("select * from kiosk_published_versions where id = %(id)s and business_id = %(business_id)s", {"id": str(version_id), "business_id": str(business_id)})
    if not row: raise HTTPException(status_code=404, detail="Published version not found.")
    return row


def _metadata(row: dict) -> dict:
    return {key: row.get(key) for key in ("id", "version_number", "config_signature", "published_by", "published_at", "source_draft_id")}


def _domains(left: dict, right: dict) -> list[dict]:
    labels = {"business": "Business and kiosk settings", "categories": "Categories", "products": "Menu items", "modifier_groups": "Add-on groups", "modifier_options": "Add-ons", "combos": "Combos", "combo_sections": "Combo sections", "combo_options": "Combo options"}
    output = []
    for key, label in labels.items():
        current = left.get(key); other = right.get(key)
        if isinstance(current, list) or isinstance(other, list):
            a = {str(row.get("id")): row for row in (current or [])}; b = {str(row.get("id")): row for row in (other or [])}; changed = [item for item in a.keys() | b.keys() if a.get(item) != b.get(item)]
        else: changed = [key] if current != other else []
        output.append({"key": key, "label": label, "changed": len(changed), "ids": changed})
    return output
