"""Smoke tests for application startup and the health endpoint."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_ok() -> None:
    # Using the context manager runs the lifespan (logging + DB init/dispose).
    with TestClient(create_app()) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["env"] == "test"
    assert "version" in body
