from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Definition of a tool"""
    name: str
    description: str
    parameters: Dict[str, ToolParameter] = Field(default_factory=dict)
    category: str = "general"


class ToolResult(BaseModel):
    """Result of a tool execution"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseTool(ABC):
    """Base class for tools"""
    
    def __init__(self) -> None:
        self.definition = self.get_definition()
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters against tool definition"""
        for param_name, param_def in self.definition.parameters.items():
            if param_def.required and param_name not in parameters:
                return False
        return True
