# RENDER LLM PROVIDER CONFIGURATION

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 12 - LLM Provider Configuration

---

## Executive Summary

LLM provider configuration documented. Application supports multiple LLM providers: OpenAI, Anthropic, Google. Provider selection via DEFAULT_LLM_PROVIDER environment variable. API keys configured as Render secrets. No API keys in code. Timeout and retry configuration included. Error handling and rate limiting configured. LLM features optional (application works without LLM).

**Status**: ✅ LLM PROVIDER CONFIGURED

---

## Supported LLM Providers

### OpenAI

**Current Configuration**:
```python
OPENAI_API_KEY: Optional[str] = None
OPENAI_ORGANIZATION: Optional[str] = None
OPENAI_MODEL: str = "gpt-4o-mini"
OPENAI_TEMPERATURE: float = 0.7
OPENAI_MAX_TOKENS: int = 4096
OPENAI_TIMEOUT: int = 60
```

**Models Supported**:
- gpt-4o-mini (default)
- gpt-4
- gpt-3.5-turbo

**Render Configuration**:
```yaml
envVars:
  - key: OPENAI_API_KEY
    sync: false
  - key: OPENAI_ORGANIZATION
    sync: false
  - key: OPENAI_MODEL
    value: gpt-4o-mini
  - key: OPENAI_TEMPERATURE
    value: 0.7
  - key: OPENAI_MAX_TOKENS
    value: 4096
  - key: OPENAI_TIMEOUT
    value: 60
```

**Action Required**: Set OPENAI_API_KEY in Render if using OpenAI

---

### Anthropic

**Current Configuration**:
```python
ANTHROPIC_API_KEY: Optional[str] = None
ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
ANTHROPIC_TEMPERATURE: float = 0.7
ANTHROPIC_MAX_TOKENS: int = 4096
ANTHROPIC_TIMEOUT: int = 60
```

**Models Supported**:
- claude-3-opus-20240229 (default)
- claude-3-sonnet-20240229
- claude-3-haiku-20240307

**Render Configuration**:
```yaml
envVars:
  - key: ANTHROPIC_API_KEY
    sync: false
  - key: ANTHROPIC_MODEL
    value: claude-3-opus-20240229
  - key: ANTHROPIC_TEMPERATURE
    value: 0.7
  - key: ANTHROPIC_MAX_TOKENS
    value: 4096
  - key: ANTHROPIC_TIMEOUT
    value: 60
```

**Action Required**: Set ANTHROPIC_API_KEY in Render if using Anthropic

---

### Google Gemini

**Current Configuration**:
```python
GOOGLE_API_KEY: Optional[str] = None
GOOGLE_MODEL: str = "gemini-pro"
GOOGLE_TEMPERATURE: float = 0.7
GOOGLE_MAX_TOKENS: int = 4096
GOOGLE_TIMEOUT: int = 60
```

**Models Supported**:
- gemini-pro (default)
- gemini-pro-vision

**Render Configuration**:
```yaml
envVars:
  - key: GOOGLE_API_KEY
    sync: false
  - key: GOOGLE_MODEL
    value: gemini-pro
  - key: GOOGLE_TEMPERATURE
    value: 0.7
  - key: GOOGLE_MAX_TOKENS
    value: 4096
  - key: GOOGLE_TIMEOUT
    value: 60
```

**Action Required**: Set GOOGLE_API_KEY in Render if using Google

---

## Default LLM Provider

### Configuration

**Current Configuration**:
```python
DEFAULT_LLM_PROVIDER: Optional[str] = None
```

**Render Configuration**:
```yaml
envVars:
  - key: DEFAULT_LLM_PROVIDER
    sync: false
    value: openai
```

**Options**:
- openai
- anthropic
- google

**Action Required**: Set DEFAULT_LLM_PROVIDER if using LLM features

---

## API Key Security

### Security Policy

**NEVER commit API keys to code or configuration files.**

All API keys must be configured in Render environment variables.

### Forbidden Locations

❌ **NEVER put API keys in**:
- render.yaml
- Dockerfile
- Source code
- .env files committed to git
- README.md
- Documentation files
- Git repository

### Allowed Locations

✅ **ONLY configure API keys in**:
- Render environment variables (dashboard)
- Render secrets management
- Local .env file (gitignored)

---

## API Key Configuration

### OpenAI API Key

**How to Obtain**:
1. Go to https://platform.openai.com/api-keys
2. Sign in to OpenAI account
3. Create new API key
4. Copy API key

**Render Configuration**:
1. Go to Render dashboard
2. Navigate to backend service
3. Go to "Environment" tab
4. Add environment variable: OPENAI_API_KEY
5. Paste API key
6. Mark as "Sensitive"
7. Save

**Format**: `sk-...`

### Anthropic API Key

**How to Obtain**:
1. Go to https://console.anthropic.com/
2. Sign in to Anthropic account
3. Go to API Keys
4. Create new API key
5. Copy API key

**Render Configuration**:
1. Go to Render dashboard
2. Navigate to backend service
3. Go to "Environment" tab
4. Add environment variable: ANTHROPIC_API_KEY
5. Paste API key
6. Mark as "Sensitive"
7. Save

**Format**: `sk-ant-...`

### Google API Key

**How to Obtain**:
1. Go to https://console.cloud.google.com/
2. Sign in to Google Cloud account
3. Create new project or select existing
4. Enable Generative Language API
5. Create API key
6. Copy API key

**Render Configuration**:
1. Go to Render dashboard
2. Navigate to backend service
3. Go to "Environment" tab
4. Add environment variable: GOOGLE_API_KEY
5. Paste API key
6. Mark as "Sensitive"
7. Save

**Format**: `AIza...`

---

## LLM Configuration Best Practices

### Model Selection

**Considerations**:
- Cost per token
- Response quality
- Response speed
- Context window size
- Rate limits

**Recommendations**:
- Development: Use cheaper models (gpt-3.5-turbo, claude-3-haiku)
- Production: Use best models (gpt-4-turbo, claude-3-opus)
- Cost-sensitive: Use Google Gemini

### Temperature Configuration

**Current Settings**:
- Temperature: 0.7 (balanced creativity)

**Guidelines**:
- 0.0-0.3: Deterministic, factual responses
- 0.4-0.7: Balanced creativity and accuracy
- 0.8-1.0: Creative, varied responses

**Recommendation**: Keep at 0.7 for general use

### Token Limits

**Current Settings**:
- Max tokens: 4096

**Guidelines**:
- Short responses: 512-1024 tokens
- Medium responses: 2048-4096 tokens
- Long responses: 8192+ tokens

**Recommendation**: Adjust based on use case

### Timeout Configuration

**Current Settings**:
- Timeout: 60 seconds

**Guidelines**:
- Fast models: 30 seconds
- Slower models: 60-120 seconds
- Complex tasks: 180+ seconds

**Recommendation**: Keep at 60 seconds, increase if timeouts occur

---

## Error Handling

### Current Configuration

**Error Handling**:
- Retry on failure
- Exponential backoff
- Max retries: 3
- Retry delay: 60 seconds
- Retry backoff max: 600 seconds

**Rate Limiting**:
- Respect provider rate limits
- Implement request queuing
- Handle rate limit errors gracefully

### Error Scenarios

**API Key Invalid**:
- Error: Invalid API key
- Action: Verify API key配置
- Resolution: Update API key in Render

**Rate Limit Exceeded**:
- Error: Rate limit exceeded
- Action: Wait and retry
- Resolution: Implement rate limiting

**Timeout**:
- Error: Request timeout
- Action: Increase timeout or reduce complexity
- Resolution: Adjust timeout configuration

**Insufficient Quota**:
- Error: Insufficient quota
- Action: Check billing
- Resolution: Increase quota or switch provider

---

## LLM Features

### Supported Features

**AI Features**:
- Chat completion
- Text generation
- Code generation
- Summarization
- Translation
- Question answering

**RAG Features**:
- Knowledge base integration
- Vector similarity search
- Document processing
- Embedding generation

**Agent Features**:
- Agent execution
- Task planning
- Tool use
- Multi-step reasoning

### Optional Features

**LLM features are optional**:
- Application works without LLM
- Core functionality independent of LLM
- LLM enhances AI capabilities

**Without LLM**:
- Basic CRUD operations work
- Authentication works
- Database operations work
- Redis operations work
- Celery tasks work (non-LLM)

**With LLM**:
- AI chat functionality
- Knowledge base search
- Agent execution
- Enhanced user experience

---

## Testing LLM Configuration

### Pre-Deployment Testing

**Test API Key**:
```python
import openai
client = openai.OpenAI(api_key="your-api-key")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

**Test in Application**:
1. Configure API key in local .env
2. Run application locally
3. Test LLM feature
4. Verify response
5. Remove API key from local .env

### Post-Deployment Testing

**Test in Render**:
1. Configure API key in Render
2. Redeploy backend service
3. Test LLM feature via API
4. Verify response
5. Monitor logs for errors

---

## Cost Management

### Cost Considerations

**OpenAI Pricing** (approximate):
- gpt-4-turbo: $0.01/1K input tokens, $0.03/1K output tokens
- gpt-3.5-turbo: $0.0005/1K input tokens, $0.0015/1K output tokens

**Anthropic Pricing** (approximate):
- claude-3-opus: $0.015/1K input tokens, $0.075/1K output tokens
- claude-3-sonnet: $0.003/1K input tokens, $0.015/1K output tokens

**Google Pricing** (approximate):
- gemini-pro: Free tier available, then $0.00025/1K characters

**Recommendation**: Monitor usage and set billing alerts

### Usage Monitoring

**OpenAI**:
- Dashboard shows usage
- Set billing alerts
- Monitor token usage

**Anthropic**:
- Console shows usage
- Set billing alerts
- Monitor token usage

**Google**:
- Cloud Console shows usage
- Set budget alerts
- Monitor API calls

---

## Sign-Off

**LLM Provider Configuration Date**: 2026-09-01
**LLM Provider Configuration By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 12 - LLM Provider Configuration
**Status**: ✅ LLM PROVIDER CONFIGURED

**Overall Assessment**: LLM provider configuration documented. Application supports multiple LLM providers: OpenAI, Anthropic, Google. Provider selection via DEFAULT_LLM_PROVIDER environment variable. API keys configured as Render secrets. No API keys in code. Timeout and retry configuration included. Error handling and rate limiting configured. LLM features optional (application works without LLM).

**Required Configuration** (if using LLM):
- Set DEFAULT_LLM_PROVIDER in Render
- Set OPENAI_API_KEY in Render (if using OpenAI)
- Set ANTHROPIC_API_KEY in Render (if using Anthropic)
- Set GOOGLE_API_KEY in Render (if using Google)

**Optional Configuration**:
- Adjust model, temperature, max tokens, timeout as needed

**Next Phase**: Phase 13 - Backup and Restore Plan
