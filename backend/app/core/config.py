from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Any
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Application
    APP_NAME: str = "Jarvis AI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    APP_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://jarvis:changeme@localhost:5432/jarvis"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    REDIS_MAX_CONNECTIONS: int = 50

    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "X-Requested-With"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORGANIZATION: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TIMEOUT: int = 60

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TIMEOUT: int = 60

    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-pro"
    GOOGLE_TEMPERATURE: float = 0.7
    GOOGLE_MAX_TOKENS: int = 4096
    GOOGLE_TIMEOUT: int = 60

    # Default LLM Provider
    DEFAULT_LLM_PROVIDER: str = "openai"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TIMEOUT: int = 120

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3-opus"
    OPENROUTER_TEMPERATURE: float = 0.7
    OPENROUTER_TIMEOUT: int = 60

    # Default LLM Provider
    DEFAULT_LLM_PROVIDER: Optional[str] = None

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "jarvis_memory"
    CHROMA_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TRACKED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600

    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "doc", "docx", "txt", "md", "json", "csv",
        "xlsx", "pptx", "png", "jpg", "jpeg", "gif", "bmp", "webp"
    ]
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/json",
        "application/octet-stream",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_DIR: str = "./logs"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "30 days"

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "jarvis-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@jarvis-ai.com"
    SMTP_TLS: bool = True

    # OAuth2
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/google/callback"

    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None
    GITHUB_OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/github/callback"

    # Browser Automation
    SELENIUM_DRIVER: str = "chrome"
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 30

    # Voice
    VOICE_ENABLED: bool = True
    VOICE_LANGUAGE: str = "en-US"
    VOICE_STT_ENGINE: str = "whisper"
    VOICE_TTS_ENGINE: str = "piper"
    
    # Whisper (Speech-to-Text)
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_SAMPLE_RATE: int = 16000
    WHISPER_CHUNK_LENGTH: int = 30
    WHISPER_LANGUAGE: Optional[str] = None
    
    # TTS (Text-to-Speech)
    TTS_VOICE: str = "en_US-amy-medium"
    TTS_SPEED: float = 1.0
    TTS_PITCH: float = 1.0
    TTS_SAMPLE_RATE: int = 22050
    
    # Wake Word
    WAKE_WORD_ENABLED: bool = True
    WAKE_WORD_PHRASE: str = "hey jarvis"
    WAKE_WORD_SENSITIVITY: float = 0.5
    WAKE_WORD_MODEL: str = "porcupine"

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # Calendar
    GOOGLE_CALENDAR_CREDENTIALS_PATH: str = "./credentials/google-calendar.json"
    GOOGLE_CALENDAR_TOKEN_PATH: str = "./credentials/google-calendar-token.json"

    # Feature Flags
    ENABLE_BROWSE: bool = True
    ENABLE_TERMINAL: bool = True
    ENABLE_GITHUB: bool = True
    ENABLE_VOICE: bool = True
    ENABLE_IMAGE: bool = True
    ENABLE_DOCUMENT: bool = True
    ENABLE_CALENDAR: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_VISION: bool = True
    ENABLE_COMPUTER_USE: bool = True
    
    # Computer Use & Automation
    COMPUTER_USE_SANDBOXED: bool = True
    COMPUTER_USE_ALLOWED_PATHS: List[str] = ["./data/computer"]
    COMPUTER_USE_MAX_FILE_SIZE: int = 104857600  # 100MB
    COMPUTER_USE_COMMAND_TIMEOUT: int = 300  # 5 minutes
    COMPUTER_USE_BROWSER_TIMEOUT: int = 60
    COMPUTER_USE_PERMISSION_DURATION: int = 3600  # 1 hour
    COMPUTER_USE_AUDIT_LOG_ENABLED: bool = True
    
    # Playwright (Browser Automation)
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_BROWSER: str = "chromium"
    PLAYWRIGHT_DOWNLOAD_PATH: str = "./data/playwright"
    
    # File System
    FILE_SYSTEM_MAX_DEPTH: int = 10
    FILE_SYSTEM_MAX_RESULTS: int = 1000

    # Vision / OCR
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    TESSERACT_LANGUAGES: str = "eng+fra+deu+spa+ita+por+chi_sim+jpn"
    VISION_MAX_IMAGE_SIZE: int = 10485760  # 10MB
    VISION_SUPPORTED_FORMATS: List[str] = ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"]
    VISION_OCR_CONFIDENCE_THRESHOLD: float = 0.6
    VISION_OBJECT_DETECTION_CONFIDENCE: float = 0.5

    # Admin
    ADMIN_EMAIL: str = "admin@jarvis-ai.com"
    ADMIN_PASSWORD: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.APP_ENV == "production" and not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")
        if self.APP_ENV == "production" and not self.ADMIN_PASSWORD:
            raise ValueError("ADMIN_PASSWORD must be set in production")

        if self.APP_ENV != "production":
            self.SECRET_KEY = self.SECRET_KEY or "dev-secret-key"
            self.ADMIN_PASSWORD = self.ADMIN_PASSWORD or "dev-password"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
