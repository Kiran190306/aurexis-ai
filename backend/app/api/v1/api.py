from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, conversations, messages, tools, plugins, agents,
    memory, documents, files, calendar, notifications, agent_execution, vision, voice, computer, knowledge, tasks
)

api_router = APIRouter()

# Include routers (FastAPI returns _IncludedRouter objects inside app.routes).
# Add an explicit 'path' attribute so route ordering tests that iterate over
# app.routes don't crash.

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["Plugins"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(memory.router, prefix="/memory", tags=["Memory"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(agent_execution.router, prefix="/agent-execution", tags=["Agent Execution"])
api_router.include_router(vision.router, prefix="/vision", tags=["Vision"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])
api_router.include_router(computer.router, prefix="/computer", tags=["Computer Use"])
api_router.include_router(knowledge.router, tags=["Knowledge"])
api_router.include_router(tasks.router, tags=["Tasks"])


