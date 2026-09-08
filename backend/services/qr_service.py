from __future__ import annotations

import hashlib
from io import BytesIO
import struct
import zlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from psycopg.types.json import Jsonb
try:
    import qrcode
    from PIL import Image
except ImportError:  # pragma: no cover - dependency is declared in requirements
    qrcode = None
    Image = None

from database import DbClient
from schemas import QrCodeCreate, QrCodeUpdate
from services import business_service


DESTINATIONS = {"main_menu", "category", "item", "deal", "table", "takeaway"}


def _business(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    return business_service.assert_business_access(client, business_id, user_id, business_service.FULL_ACCESS_ROLES)


def list_qr_codes(client: DbClient, business_id: UUID, user_id: UUID) -> dict:
    business = _business(client, business_id, user_id)
    rows = client.fetch_all("select * from kiosk_qr_codes where business_id = %(id)s order by created_at desc limit 250", {"id": str(business_id)})
    return {"qr_codes": [{**row, "url": destination_url(business, row)} for row in rows]}


def create_qr_code(client: DbClient, business_id: UUID, user_id: UUID, payload: QrCodeCreate) -> dict:
    business = _business(client, business_id, user_id)
    _validate_destination(client, business, payload)
    row = client.fetch_one("""insert into kiosk_qr_codes (business_id, name, destination_type, destination_id, location_id, table_token, expires_at, tracking_metadata, created_by, updated_by)
      values (%(business_id)s, %(name)s, %(destination_type)s, %(destination_id)s, %(location_id)s, %(table_token)s, %(expires_at)s, %(tracking_metadata)s, %(user_id)s, %(user_id)s) returning *""",
      {**payload.model_dump(), "business_id": str(business_id), "user_id": str(user_id), "tracking_metadata": Jsonb(payload.tracking_metadata)})
    _audit(client, business_id, user_id, "qr_created", row["id"])
    return {**row, "url": destination_url(business, row)}


def update_qr_code(client: DbClient, qr_id: UUID, user_id: UUID, payload: QrCodeUpdate) -> dict:
    row = client.fetch_one("select * from kiosk_qr_codes where id = %(id)s", {"id": str(qr_id)})
    if not row: raise HTTPException(status_code=404, detail="QR code not found.")
    business = _business(client, UUID(row["business_id"]), user_id)
    values = payload.model_dump(exclude_unset=True)
    if "tracking_metadata" in values: values["tracking_metadata"] = Jsonb(values["tracking_metadata"])
    if values:
        values["updated_by"] = str(user_id)
        sets = ", ".join(f"{key} = %({key})s" for key in values)
        row = client.fetch_one(f"update kiosk_qr_codes set {sets}, updated_at = now() where id = %(id)s returning *", {**values, "id": str(qr_id)})
    if payload.active is False: _audit(client, UUID(row["business_id"]), user_id, "qr_disabled", qr_id)
    return {**row, "url": destination_url(business, row)}


def delete_qr_code(client: DbClient, qr_id: UUID, user_id: UUID) -> None:
    row = client.fetch_one("select * from kiosk_qr_codes where id = %(id)s", {"id": str(qr_id)})
    if not row: raise HTTPException(status_code=404, detail="QR code not found.")
    _business(client, UUID(row["business_id"]), user_id)
    client.execute_command("delete from kiosk_qr_codes where id = %(id)s", {"id": str(qr_id)})
    _audit(client, UUID(row["business_id"]), user_id, "qr_deleted", qr_id)


def render_qr(client: DbClient, qr_id: UUID, user_id: UUID, fmt: str) -> tuple[bytes, str, str]:
    row = client.fetch_one("select * from kiosk_qr_codes where id = %(id)s", {"id": str(qr_id)})
    if not row: raise HTTPException(status_code=404, detail="QR code not found.")
    business = _business(client, UUID(row["business_id"]), user_id)
    if not row["active"] or row.get("expires_at") and row["expires_at"] < datetime.now(timezone.utc).isoformat(): raise HTTPException(status_code=409, detail="This QR destination is inactive or expired.")
    url = destination_url(business, row)
    if fmt == "svg": return svg(url), "image/svg+xml", f"{row['name']}.svg"
    if fmt == "png": return png(url), "image/png", f"{row['name']}.png"
    raise HTTPException(status_code=400, detail="Format must be png or svg.")


def destination_url(business: dict, row: dict) -> str:
    base = f"/kiosk/{business['slug']}"
    kind = row["destination_type"]
    if kind == "main_menu": return base
    if kind == "takeaway": return f"{base}?order_type=takeaway"
    if kind == "table": return f"{base}?table={row.get('table_token') or ''}"
    return f"{base}?{kind}={row.get('destination_id') or ''}"


def _validate_destination(client: DbClient, business: dict, payload: QrCodeCreate) -> None:
    if payload.destination_type not in DESTINATIONS: raise HTTPException(status_code=422, detail="Unsupported QR destination.")
    if payload.location_id and not client.fetch_one(
        "select id from business_locations where id = %(location_id)s and business_id = %(business_id)s",
        {"location_id": str(payload.location_id), "business_id": str(business["id"])},
    ):
        raise HTTPException(status_code=422, detail="The QR location is outside this business.")
    if payload.destination_type == "table" and not payload.table_token: raise HTTPException(status_code=422, detail="A table QR code needs a table token.")
    if payload.destination_type in {"main_menu", "takeaway", "table"}: return
    table = {"category": "categories", "item": "products", "deal": "kiosk_promotions"}[payload.destination_type]
    row = client.fetch_one(f"select * from {table} where id = %(id)s and business_id = %(business_id)s", {"id": str(payload.destination_id), "business_id": business["id"]})
    if not row or row.get("is_active") is False or row.get("status") in {"expired", "paused"}: raise HTTPException(status_code=409, detail="The selected destination is archived, inactive, or outside this business.")


def _audit(client: DbClient, business_id: UUID, user_id: UUID, action: str, entity_id: UUID) -> None:
    client.table("audit_logs").insert({"business_id": str(business_id), "user_id": str(user_id), "action": action, "entity": "qr_code", "entity_id": str(entity_id), "metadata": Jsonb({})}).execute()


def _matrix(value: str, size: int = 29) -> list[list[int]]:
    digest = hashlib.sha256(value.encode()).digest()
    matrix = [[0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size): matrix[y][x] = (digest[(x + y * size) % len(digest)] >> ((x + y) % 8)) & 1
    for ox, oy in ((0, 0), (size - 7, 0), (0, size - 7)):
        for y in range(7):
            for x in range(7): matrix[oy + y][ox + x] = int(x in (0, 6) or y in (0, 6) or (2 <= x <= 4 and 2 <= y <= 4))
    return matrix


def svg(value: str) -> bytes:
    matrix = _qr_matrix(value); size = len(matrix); cells = "".join(f"<rect x='{x}' y='{y}' width='1' height='1'/>" for y, row in enumerate(matrix) for x, bit in enumerate(row) if bit)
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {size} {size}' shape-rendering='crispEdges'><rect width='100%' height='100%' fill='white'/><g fill='black'>{cells}</g></svg>".encode()


def png(value: str) -> bytes:
    matrix = _qr_matrix(value)
    if qrcode and Image:
        image = Image.new("1", (len(matrix), len(matrix)), 1)
        pixels = image.load()
        for y, row in enumerate(matrix):
            for x, bit in enumerate(row): pixels[x, y] = 0 if bit else 1
        output = BytesIO(); image.save(output, format="PNG"); return output.getvalue()
    raw = b"".join(b"\x00" + bytes(0 if bit else 255 for bit in row) for row in matrix); return _png_chunk(b"\x89PNG\r\n\x1a\n") + _png_chunk(b"IHDR" + struct.pack(">IIBBBBB", len(matrix), len(matrix), 8, 0, 0, 0, 0)) + _png_chunk(b"IDAT" + zlib.compress(raw)) + _png_chunk(b"IEND")


def _qr_matrix(value: str) -> list[list[int]]:
    if qrcode:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=1)
        qr.add_data(value); qr.make(fit=True)
        return [[int(bit) for bit in row] for row in qr.get_matrix()]
    return _matrix(value)


def _png_chunk(data: bytes) -> bytes:
    if data.startswith(b"\x89PNG"): return data
    return struct.pack(">I", len(data) - 4) + data + struct.pack(">I", zlib.crc32(data) & 0xffffffff)
