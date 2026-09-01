from typing import List, Optional, AsyncIterator, Any
from anthropic import AsyncAnthropic
from .base import BaseLLMProvider, Message, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", **kwargs: Any) -> None:
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response from Anthropic"""
        # Convert messages to Anthropic format
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})
        
        response = await self.client.messages.create(  # type: ignore[attr-defined]
            model=self.model,
            messages=anthropic_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            **kwargs
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Generate a streaming response from Anthropic"""
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({"role": msg.role, "content": msg.content})
        
        async with self.client.messages.stream(  # type: ignore[attr-defined]
            model=self.model,
            messages=anthropic_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def count_tokens(self, text: str) -> int:
        """Approximate token count for Anthropic (roughly 4 chars per token)"""
        return len(text) // 4
