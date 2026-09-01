from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse

from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import settings
from app.main import app as backend_app


def test_security_headers_are_added():
    app = Starlette()

    async def home(request):
        return PlainTextResponse("ok")

    app.add_route("/", home)
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers


def test_rate_limit_returns_429_after_threshold(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 2)

    app = Starlette()

    async def home(request):
        return JSONResponse({"ok": True})

    app.add_route("/", home)
    app.add_middleware(RateLimitMiddleware)
    client = TestClient(app)

    first = client.get("/")
    second = client.get("/")
    third = client.get("/")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert "Retry-After" in third.headers


def test_request_and_correlation_ids_are_propagated():
    client = TestClient(backend_app)
    response = client.get("/", headers={"X-Correlation-ID": "release-candidate-test"})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "release-candidate-test"
    assert response.headers["X-Request-ID"]
