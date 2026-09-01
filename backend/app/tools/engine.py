from typing import Dict, List, Any, Optional
from .base import BaseTool, ToolDefinition, ToolResult
from .web_search import WebSearchTool
from loguru import logger
import json


class ToolCallingEngine:
    """Engine for managing and executing tools"""
    
    def __init__(self) -> None:
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default tools"""
        self.register_tool(WebSearchTool())
        # Do not register the legacy host-process executor. It cannot honestly
        # provide an isolation boundary and would permit an LLM/tool caller to
        # execute arbitrary code inside the API container.
        logger.info("Safe default tools registered")
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool"""
        self.tools[tool.definition.name] = tool
        logger.info(f"Registered tool: {tool.definition.name}")
    
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools"""
        return [tool.definition for tool in self.tools.values()]
    
    def list_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """List tools by category"""
        return [
            tool.definition 
            for tool in self.tools.values() 
            if tool.definition.category == category
        ]
    
    async def execute_tool(
        self,
        name: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool with given parameters"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        # Validate parameters
        if not tool.validate_parameters(parameters):
            return ToolResult(
                success=False,
                error="Invalid or missing required parameters"
            )
        
        logger.info(f"Executing tool: {name}")
        
        try:
            result = await tool.execute(**parameters)
            logger.info(f"Tool {name} executed: success={result.success}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def get_tool_schema(self) -> str:
        """Get the tool schema for LLM function calling"""
        tools_schema = []
        
        for tool in self.tools.values():
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.definition.name,
                    "description": tool.definition.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            for param_name, param_def in tool.definition.parameters.items():
                tool_schema["function"]["parameters"]["properties"][param_name] = {  # type: ignore[index]
                    "type": param_def.type,
                    "description": param_def.description
                }
                if param_def.default is not None:
                    tool_schema["function"]["parameters"]["properties"][param_name]["default"] = param_def.default  # type: ignore[index]
                if param_def.required:
                    tool_schema["function"]["parameters"]["required"].append(param_name)  # type: ignore[index]
            
            tools_schema.append(tool_schema)
        
        return json.dumps(tools_schema, indent=2)
    
    def parse_tool_call(self, tool_call: str) -> tuple[str, Dict[str, Any]]:
        """Parse a tool call from LLM response"""
        try:
            # Parse JSON tool call
            call_data = json.loads(tool_call)
            tool_name = call_data.get("name")
            parameters = call_data.get("parameters", {})
            return tool_name, parameters
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call: {e}")
            raise ValueError("Invalid tool call format")


# Global tool calling engine instance
tool_engine = ToolCallingEngine()
