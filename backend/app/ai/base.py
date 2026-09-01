from abc import ABC, abstractmethod
from typing import List, Optional, Any, AsyncIterator
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str, **kwargs: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Generate a streaming response from the LLM"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        pass
