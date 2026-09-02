"""
Tests for application settings configuration parsing.
Tests string/list compatibility for ALLOWED_HOSTS and CORS_ORIGINS.
"""
import pytest
from pydantic import ValidationError
from app.core.config import Settings


class TestSettingsParsing:
    """Test settings parsing for string/list compatibility."""

    def test_allowed_hosts_single_string(self):
        """Test ALLOWED_HOSTS accepts a single hostname string."""
        settings = Settings(ALLOWED_HOSTS="aurexis-backend.onrender.com")
        assert settings.ALLOWED_HOSTS == ["aurexis-backend.onrender.com"]

    def test_allowed_hosts_comma_separated(self):
        """Test ALLOWED_HOSTS accepts comma-separated hostnames."""
        settings = Settings(ALLOWED_HOSTS="aurexis-backend.onrender.com,localhost,127.0.0.1")
        assert settings.ALLOWED_HOSTS == ["aurexis-backend.onrender.com", "localhost", "127.0.0.1"]

    def test_allowed_hosts_list(self):
        """Test ALLOWED_HOSTS accepts a list of hostnames."""
        settings = Settings(ALLOWED_HOSTS=["aurexis-backend.onrender.com", "localhost"])
        assert settings.ALLOWED_HOSTS == ["aurexis-backend.onrender.com", "localhost"]

    def test_allowed_hosts_default(self):
        """Test ALLOWED_HOSTS uses default when not provided."""
        settings = Settings()
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "0.0.0.0"]

    def test_cors_origins_single_string(self):
        """Test CORS_ORIGINS accepts a single origin string."""
        settings = Settings(CORS_ORIGINS="https://aurexis-frontend.onrender.com")
        assert settings.CORS_ORIGINS == ["https://aurexis-frontend.onrender.com"]

    def test_cors_origins_comma_separated(self):
        """Test CORS_ORIGINS accepts comma-separated origins."""
        settings = Settings(CORS_ORIGINS="https://aurexis-frontend.onrender.com,http://localhost:3000")
        assert settings.CORS_ORIGINS == ["https://aurexis-frontend.onrender.com", "http://localhost:3000"]

    def test_cors_origins_list(self):
        """Test CORS_ORIGINS accepts a list of origins."""
        settings = Settings(CORS_ORIGINS=["https://aurexis-frontend.onrender.com", "http://localhost:3000"])
        assert settings.CORS_ORIGINS == ["https://aurexis-frontend.onrender.com", "http://localhost:3000"]

    def test_cors_origins_default(self):
        """Test CORS_ORIGINS uses default when not provided."""
        settings = Settings()
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    def test_allowed_hosts_with_whitespace(self):
        """Test ALLOWED_HOSTS handles whitespace in comma-separated values."""
        settings = Settings(ALLOWED_HOSTS=" aurexis-backend.onrender.com , localhost , 127.0.0.1 ")
        assert settings.ALLOWED_HOSTS == ["aurexis-backend.onrender.com", "localhost", "127.0.0.1"]

    def test_cors_origins_with_whitespace(self):
        """Test CORS_ORIGINS handles whitespace in comma-separated values."""
        settings = Settings(CORS_ORIGINS=" https://aurexis-frontend.onrender.com , http://localhost:3000 ")
        assert settings.CORS_ORIGINS == ["https://aurexis-frontend.onrender.com", "http://localhost:3000"]

    def test_render_deployment_scenario(self):
        """Test the exact Render deployment scenario with dynamic service URLs."""
        settings = Settings(
            APP_ENV="production",
            ALLOWED_HOSTS="aurexis-backend.onrender.com",
            CORS_ORIGINS="https://aurexis-frontend.onrender.com",
            SECRET_KEY="test-secret-key",
            ADMIN_PASSWORD="test-password"
        )
        assert settings.ALLOWED_HOSTS == ["aurexis-backend.onrender.com"]
        assert settings.CORS_ORIGINS == ["https://aurexis-frontend.onrender.com"]

    def test_local_development_scenario(self):
        """Test local development scenario with default values."""
        settings = Settings(APP_ENV="development")
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "0.0.0.0"]
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    def test_database_url_postgres_to_asyncpg(self):
        """Test DATABASE_URL normalization: postgres:// -> postgresql+asyncpg://"""
        settings = Settings(DATABASE_URL="postgres://user:pass@localhost:5432/db")
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_database_url_postgresql_to_asyncpg(self):
        """Test DATABASE_URL normalization: postgresql:// -> postgresql+asyncpg://"""
        settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/db")
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_database_url_psycopg2_to_asyncpg(self):
        """Test DATABASE_URL normalization: postgresql+psycopg2:// -> postgresql+asyncpg://"""
        settings = Settings(DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/db")
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_database_url_asyncpg_unchanged(self):
        """Test DATABASE_URL normalization: postgresql+asyncpg:// remains unchanged"""
        settings = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db")
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_database_url_sqlite_unchanged(self):
        """Test DATABASE_URL normalization: SQLite URLs remain unchanged"""
        settings = Settings(DATABASE_URL="sqlite:///./test.db")
        assert settings.DATABASE_URL == "sqlite:///./test.db"

    def test_database_url_render_scenario(self):
        """Test DATABASE_URL normalization for Render fromDatabase connectionString"""
        settings = Settings(DATABASE_URL="postgres://jarvis:password@host:5432/jarvis")
        assert settings.DATABASE_URL == "postgresql+asyncpg://jarvis:password@host:5432/jarvis"
