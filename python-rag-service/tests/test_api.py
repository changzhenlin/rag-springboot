from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_rag_health_endpoint() -> None:
    response = client.get("/api/rag/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["status"] == "UP"


def test_test_health_endpoint() -> None:
    response = client.get("/api/test/health")
    assert response.status_code == 200
    payload = response.json()
    assert "chatClientAvailable" in payload


def test_upload_rejects_unsupported_file() -> None:
    response = client.post(
        "/api/rag/upload",
        files={"file": ("bad.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == 400
