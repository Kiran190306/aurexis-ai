"""
Pydantic schemas for agent execution API.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ExecutionRequest(BaseModel):
    """Request for agent execution."""
    request: str = Field(..., description="User request to process")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    conversation_id: Optional[int] = Field(default=None, description="Conversation ID")
    enable_reflection: bool = Field(default=True, description="Enable reflection agent for quality check")


class ExecutionPlanCreate(BaseModel):
    """Schema for creating execution plan."""
    user_request: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[int] = None


class ExecutionPlanResponse(BaseModel):
    """Response for execution plan."""
    id: int
    uuid: str
    user_id: int
    conversation_id: Optional[int]
    user_request: str
    context: Optional[Dict[str, Any]]
    plan_data: Dict[str, Any]
    task_count: int
    estimated_duration_seconds: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_seconds: Optional[float]
    final_output: Optional[Dict[str, Any]]
    result_summary: Optional[str]
    error_message: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExecutionPlanStatus(BaseModel):
    """Status of execution plan."""
    status: str
    completed_at: Optional[datetime] = None


class ExecutionLogResponse(BaseModel):
    """Response for execution log."""
    id: int
    uuid: str
    execution_plan_id: int
    agent_id: Optional[int]
    task_id: str
    task_type: str
    agent_role: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time_seconds: Optional[float]
    retry_count: int
    timeout_seconds: Optional[int]
    error_message: Optional[str]
    error_code: Optional[str]
    depends_on: Optional[List[str]]
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Response for agent execution."""
    execution_plan_id: str
    status: str
    result: Optional[Dict[str, Any]]
    summary: Optional[str]
    execution_time_seconds: Optional[float]
    metadata: Optional[Dict[str, Any]]


class AgentStatusResponse(BaseModel):
    """Response for agent status."""
    agent_id: str
    role: str
    config: Dict[str, Any]
    active_tasks: Optional[int] = None
    completed_tasks: Optional[int] = None
    failed_tasks: Optional[int] = None
    registered_agents: Optional[int] = None


class AgentCapabilitiesResponse(BaseModel):
    """Response for agent capabilities."""
    capabilities: List[str]


class EventBusStatsResponse(BaseModel):
    """Response for event bus statistics."""
    subscribers: int
    queue_size: int
    running: bool
