
import pytest
from unittest.mock import AsyncMock

from app.api.v1.endpoints.auth import refresh_token
from app.schemas.auth import TokenRefresh
from fastapi.testclient import TestClient
from app.main import app


class DummyResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(monkeypatch):
    user = type("User", (), {"id": 1})()
    session = type(
        "Session",
        (),
        {"token": "old-access", "refresh_token": "old-refresh", "is_active": True},
    )()

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[DummyResult(user), DummyResult(session)])
    db.commit = AsyncMock()

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.decode_token",
        lambda token: {"sub": "1", "type": "refresh"},
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.verify_token_type",
        lambda payload, token_type: True,
    )

    response = await refresh_token(TokenRefresh(refresh_token="refresh-token"), db=db)

    assert response.access_token
    assert response.refresh_token
    assert response.token_type == "bearer"
    assert response.expires_in > 0


def test_auth_health_endpoint_is_available():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
