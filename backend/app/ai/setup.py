from typing import Any
from .engine import ai_engine
from loguru import logger
from app.core.config import settings


async def initialize_ai_engine() -> None:
    """Initialize the AI engine with configured providers"""
    
    # Register OpenAI provider if configured
    if settings.OPENAI_API_KEY:
        ai_engine.register_provider(
            name="openai",
            provider_type="openai",
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL or "gpt-4o-mini",
        )
        logger.info("OpenAI provider initialized")
    
    # Register Anthropic provider if configured
    if settings.ANTHROPIC_API_KEY:
        ai_engine.register_provider(
            name="anthropic",
            provider_type="anthropic",
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL or "claude-3-opus-20240229",
        )
        logger.info("Anthropic provider initialized")
    
    # Set default provider only if it exists
    if settings.DEFAULT_LLM_PROVIDER and settings.DEFAULT_LLM_PROVIDER in ai_engine.list_providers():
        ai_engine.set_default_provider(settings.DEFAULT_LLM_PROVIDER)
    elif ai_engine.list_providers():
        ai_engine.set_default_provider(ai_engine.list_providers()[0])
    
    if ai_engine.list_providers():
        logger.info(f"AI Engine initialized with providers: {ai_engine.list_providers()}")
        logger.info(f"Default provider: {ai_engine.default_provider}")
    else:
        logger.warning("AI Engine initialized with no providers - LLM features will be unavailable")


def get_ai_engine() -> Any:
    """Get the global AI engine instance"""
    return ai_engine
