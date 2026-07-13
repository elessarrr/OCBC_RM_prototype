"""Smoke tests for app scaffold."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_index_returns_200() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Wealth Morning Brief" in response.text
