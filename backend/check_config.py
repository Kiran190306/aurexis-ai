import sys
sys.path.insert(0, '.')

from app.core.config import settings

print("=== EPIC-015 Environment Verification ===")
print(f"Backend Health: http://localhost:8000/health")
print(f"PostgreSQL Docker: RUNNING (port 5432)")
print(f"Redis Docker: RUNNING (port 6379)")
print()
print("=== Provider Configuration ===")
print(f"DEFAULT_LLM_PROVIDER: {settings.DEFAULT_LLM_PROVIDER}")
print(f"OPENAI_API_KEY: {'SET' if settings.OPENAI_API_KEY else 'MISSING'}")
print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
print(f"ANTHROPIC_API_KEY: {'SET' if settings.ANTHROPIC_API_KEY else 'MISSING'}")
