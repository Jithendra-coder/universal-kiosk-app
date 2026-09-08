from fastapi.testclient import TestClient

from main import MAX_REQUEST_BYTES, app


def test_declared_oversized_request_is_rejected_before_route_processing():
    with TestClient(app) as client:
        response = client.post("/api/auth/login", content=b"x" * (MAX_REQUEST_BYTES + 1))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
