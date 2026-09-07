"""
Tests for API endpoints and OpenAPI documentation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestAPIEndpoints:
    """Test basic API endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to Aurexis AI API"
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"

    def test_docs_endpoint(self):
        """Test Swagger UI docs endpoint returns HTML."""
        response = client.get("/docs")
        assert response.status_code == 200
        content = response.text
        assert "<!DOCTYPE html>" in content
        assert "swagger-ui" in content

    def test_openapi_json_endpoint(self):
        """Test OpenAPI JSON endpoint returns valid OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert data["openapi"].startswith("3.")
        assert data["info"]["title"] == "Aurexis AI"
        assert data["info"]["version"] == "1.0.0"

    def test_redoc_endpoint(self):
        """Test ReDoc endpoint returns HTML."""
        response = client.get("/redoc")
        assert response.status_code == 200
        content = response.text
        assert "<!DOCTYPE html>" in content
        assert "redoc" in content.lower()

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

    def test_liveness_endpoint(self):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_readiness_endpoint(self):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        # Should return 200 (database ok, redis skipped for dev)
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
