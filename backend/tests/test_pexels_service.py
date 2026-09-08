from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException

from services import pexels_service


def test_missing_pexels_configuration_has_no_internal_path(monkeypatch):
    monkeypatch.setattr(pexels_service, "get_settings", lambda: SimpleNamespace(pexels_api_key=None, pexels_per_page=12))
    with pytest.raises(HTTPException) as exc:
        pexels_service.search_photos("coffee")
    assert exc.value.status_code == 503
    assert exc.value.detail == "Pexels image search is not configured."


def test_rejected_pexels_credentials_are_redacted(monkeypatch):
    monkeypatch.setattr(pexels_service, "get_settings", lambda: SimpleNamespace(pexels_api_key="test-key", pexels_per_page=12))

    def reject(*_args, **_kwargs):
        raise HTTPError("https://api.pexels.com", 401, "Unauthorized", {}, BytesIO(b'{"error":"provider detail"}'))

    monkeypatch.setattr(pexels_service, "urlopen", reject)
    with pytest.raises(HTTPException) as exc:
        pexels_service.search_photos("coffee")
    assert exc.value.status_code == 502
    assert exc.value.detail == "Pexels image search credentials were rejected."
    assert "provider detail" not in exc.value.detail and ".env" not in exc.value.detail
