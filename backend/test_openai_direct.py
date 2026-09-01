import asyncio
import sys
sys.path.insert(0, '.')

from app.ai.openai_provider import OpenAIProvider
from app.ai.base import Message
from app.core.config import settings

async def test_openai():
    print(f"OPENAI_API_KEY is set: {bool(settings.OPENAI_API_KEY)}")
    print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
    print(f"DEFAULT_LLM_PROVIDER: {settings.DEFAULT_LLM_PROVIDER}")
    
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not set")
        return
    
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL or "gpt-4-turbo"
    )
    
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Reply with exactly: ORION-LLM-TEST-92841")
    ]
    
    print(f"Attempting OpenAI generation with model: {provider.model}")
    print(f"Messages: {len(messages)}")
    
    try:
        response = await provider.generate(messages)
        print(f"SUCCESS: Generated response")
        print(f"Content: {response.content}")
        print(f"Model: {response.model}")
        print(f"Tokens used: {response.tokens_used}")
        print(f"Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_openai())
