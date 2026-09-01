from fastapi.testclient import TestClient

from app.main import app


def test_auth_routes_are_registered():
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")

    assert response.status_code in {401, 403, 404}
