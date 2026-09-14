from typing import Dict, List, Optional, AsyncIterator, Any
from loguru import logger


class AIEngine:
    """Main AI engine for managing multiple LLM providers"""
    
    def __init__(self) -> None:
        self.providers: Dict[str, Any] = {}
        self.default_provider: Optional[str] = None
    
    def register_provider(
        self,
        name: str,
        provider_type: str,
        api_key: str,
        model: str,
        **kwargs: Any
    ) -> None:
        """Register a new LLM provider"""
        # Lazy import providers to avoid blocking startup
        if provider_type == "openai":
            from .openai_provider import OpenAIProvider
            self.providers[name] = OpenAIProvider(api_key, model, **kwargs)
        elif provider_type == "anthropic":
            from .anthropic_provider import AnthropicProvider
            self.providers[name] = AnthropicProvider(api_key, model, **kwargs)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        logger.info(f"Registered {provider_type} provider '{name}' with model '{model}'")
        
        if self.default_provider is None:
            self.default_provider = name
    
    def set_default_provider(self, name: str) -> None:
        """Set the default provider"""
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not found")
        self.default_provider = name
        logger.info(f"Set default provider to '{name}'")
    
    def get_provider(self, name: Optional[str] = None) -> Any:
        """Get a provider by name or default"""
        provider_name = name or self.default_provider
        if provider_name is None:
            raise ValueError("No default provider set")
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name]
    
    async def generate(
        self,
        messages: List[Any],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> Any:
        """Generate a response using the specified or default provider"""
        llm = self.get_provider(provider)
        logger.info(f"Generating response using provider '{provider or self.default_provider}'")
        logger.info(f"Provider default model: {llm.model}")
        logger.info(f"Requested model override: {model}")
        # Override model if provided
        if model:
            llm.model = model
            logger.info(f"Model overridden to: {llm.model}")
        logger.info(f"Final model being used: {llm.model}")
        logger.info(f"Temperature: {temperature}, Max tokens: {max_tokens}")
        logger.info(f"Number of messages: {len(messages)}")
        try:
            return await llm.generate(messages, temperature, max_tokens, **kwargs)
        except Exception as e:
            logger.error(f"AI engine generation error: {type(e).__name__}: {str(e)}", exc_info=True)
            logger.error(f"Error repr: {repr(e)}")
            logger.error(f"Error args: {e.args}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Any],
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Generate a streaming response using the specified or default provider"""
        llm = self.get_provider(provider)
        logger.info(f"Generating stream using provider '{provider or self.default_provider}'")
        stream = await llm.generate_stream(messages, temperature, max_tokens, **kwargs)
        async for chunk in stream:
            yield chunk
    
    async def count_tokens(
        self,
        text: str,
        provider: Optional[str] = None
    ) -> int:
        """Count tokens using the specified or default provider"""
        llm = self.get_provider(provider)
        return await llm.count_tokens(text)
    
    def list_providers(self) -> List[str]:
        """List all registered providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self, name: Optional[str] = None) -> Dict:
        """Get information about a provider"""
        llm = self.get_provider(name)
        return {
            "model": llm.model,
            "type": llm.__class__.__name__,
        }


# Global AI engine instance
ai_engine = AIEngine()
