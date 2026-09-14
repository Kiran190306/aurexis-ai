from typing import List, Optional, AsyncIterator, Any
from openai import AsyncOpenAI, RateLimitError, AuthenticationError, APIError, APIConnectionError
from .base import BaseLLMProvider, Message, LLMResponse
import tiktoken
from loguru import logger


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo", **kwargs: Any) -> None:
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        try:
            self.encoding = tiktoken.encoding_for_model(model)
            logger.info(f"Using tiktoken encoding for model: {model}")
        except KeyError:
            logger.warning(f"Model {model} not found in tiktoken, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response from OpenAI"""
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]  # type: ignore[list-item]

        logger.info(f"OpenAI API call: model={self.model}, messages={len(openai_messages)}, temperature={temperature}")
        logger.info(f"OpenAI messages: {openai_messages}")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            logger.info(f"OpenAI API response: model={response.model}, choices={len(response.choices)}, finish_reason={response.choices[0].finish_reason if response.choices else 'none'}")
            logger.info(f"OpenAI response object: {response}")
            logger.info(f"OpenAI response choices: {response.choices}")

            if not response.choices:
                raise ValueError("OpenAI API returned no choices")

            message_content = response.choices[0].message.content or ""  # type: ignore[assignment]
            logger.info(f"Extracted message content: {message_content[:100]}...")

            return LLMResponse(
                content=message_content,
                model=response.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
        except RateLimitError as e:
            logger.error(f"OpenAI RateLimitError: {str(e)}")
            error_details = {
                "error_type": "rate_limit",
                "http_status_code": getattr(e, 'status_code', 429),
                "openai_error_code": getattr(e, 'code', 'rate_limit_exceeded'),
                "openai_error_type": getattr(e, 'type', 'rate_limit'),
                "message": str(e)
            }
            logger.error(f"OpenAI rate limit error details: {error_details}")
            raise
        except AuthenticationError as e:
            logger.error(f"OpenAI AuthenticationError: {str(e)}")
            error_details = {
                "error_type": "authentication",
                "http_status_code": getattr(e, 'status_code', 401),
                "openai_error_code": getattr(e, 'code', 'invalid_api_key'),
                "openai_error_type": getattr(e, 'type', 'authentication'),
                "message": str(e)
            }
            logger.error(f"OpenAI authentication error details: {error_details}")
            raise
        except APIConnectionError as e:
            logger.error(f"OpenAI APIConnectionError: {str(e)}")
            error_details = {
                "error_type": "network",
                "message": str(e)
            }
            logger.error(f"OpenAI network error details: {error_details}")
            raise
        except APIError as e:
            logger.error(f"OpenAI APIError: {str(e)}")
            error_details = {
                "error_type": "api_error",
                "http_status_code": getattr(e, 'status_code', 500),
                "openai_error_code": getattr(e, 'code', 'api_error'),
                "openai_error_type": getattr(e, 'type', 'api_error'),
                "message": str(e)
            }
            logger.error(f"OpenAI API error details: {error_details}")
            raise
        except Exception as e:
            logger.error(f"OpenAI unexpected error: type={type(e).__name__}, message={str(e)}")
            error_details = {
                "error_type": "unexpected",
                "exception_type": type(e).__name__,
                "message": str(e)
            }
            logger.error(f"OpenAI unexpected error details: {error_details}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Generate a streaming response from OpenAI"""
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]  # type: ignore[list-item]
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        # The stream is guaranteed to be AsyncStream when stream=True
        async for chunk in stream:  # type: ignore[union-attr]
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
