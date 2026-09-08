import asyncio
import base64
from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from services import storage_service


PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC")


class Upload:
    def __init__(self, content, content_type="image/png", filename="image.png"):
        self.content = content
        self.content_type = content_type
        self.filename = filename

    async def read(self, _size):
        return self.content


def test_upload_keeps_public_path_and_sanitizes_name(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_service, "get_settings", lambda: SimpleNamespace(upload_root=str(tmp_path), public_base_url="https://api.example"))
    business_id = uuid4()
    result = asyncio.run(storage_service.upload_asset(business_id, Upload(PNG_1X1, filename="../My logo.png"), "brand"))
    assert result["path"].startswith(f"/uploads/{business_id}/brand/")
    assert result["public_url"] == f"https://api.example{result['path']}"
    assert "My-logo.png" in result["path"]
    assert (tmp_path / result["path"].removeprefix("/uploads/")).is_file()


def test_extension_must_match_verified_content(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_service, "get_settings", lambda: SimpleNamespace(upload_root=str(tmp_path), public_base_url="https://api.example"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(storage_service.upload_asset(uuid4(), Upload(PNG_1X1, filename="image.jpg"), "products"))
    assert exc.value.status_code == 400
    assert not list(tmp_path.rglob("*"))


def test_upload_rejects_image_above_pixel_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_service, "get_settings", lambda: SimpleNamespace(upload_root=str(tmp_path), public_base_url="https://api.example"))
    bomb = b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4, "big") + b"IHDR" + (10000).to_bytes(4, "big") + (10000).to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(storage_service.upload_asset(uuid4(), Upload(bomb), "products"))
    assert exc.value.status_code == 400


def test_partial_file_is_removed_after_write_failure():
    class FailedPath:
        removed = False
        mode = None

        @contextmanager
        def open(self, mode):
            self.mode = mode

            class Writer:
                def write(_self, _content):
                    raise OSError("disk failure")

            yield Writer()

        def unlink(self, missing_ok=False):
            assert missing_ok
            self.removed = True

    path = FailedPath()
    with pytest.raises(OSError):
        storage_service._write_new_file(path, b"content")
    assert path.mode == "xb" and path.removed
