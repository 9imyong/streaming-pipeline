from fastapi.testclient import TestClient

from app.gateway.main import app


def test_ui_preflight_allows_api_headers():
    client = TestClient(app)
    response = client.options(
        "/v1/sources",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type,x-request-id,x-api-key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_unlisted_origin_is_rejected():
    client = TestClient(app)
    response = client.options(
        "/v1/sources",
        headers={
            "Origin": "https://unlisted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_health_response_has_cors_headers():
    response = TestClient(app).get(
        "/health/live", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
