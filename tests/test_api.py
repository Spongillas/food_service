from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_demo_mode():
    """Без OPENROUTER_API_KEY сервис должен вернуть демо-данные, а не падать."""
    resp = client.post(
        "/api/search",
        json={"category": "упаковка", "region": "Москва", "keywords": "", "limit": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["used_ai"] is False
    assert data["warning"]
    assert len(data["suppliers"]) >= 1
    assert data["suppliers"][0]["recommended"] is True


def test_search_validates_category():
    resp = client.post("/api/search", json={"category": "a", "region": "", "keywords": "", "limit": 4})
    assert resp.status_code == 422
