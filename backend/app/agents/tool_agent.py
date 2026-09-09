"""
Tool Agent - Handles dynamic tool selection, execution, permission validation, and error recovery.
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from datetime import datetime
from .base import AgentRole, Task, AgentResponse, BaseAgent


class ToolAgent(BaseAgent):
    """Agent responsible for tool execution and management."""
    
    def __init__(self, agent_id: str = "tool", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.TOOL
        self.tool_registry: Dict[str, Dict[str, Any]] = {}
        self.tool_permissions: Dict[str, List[str]] = {}
        self.system_prompt = """You are a Tool Agent for Jarvis AI. Your role is to:
1. Select appropriate tools for given tasks
2. Execute tools with proper parameters
3. Validate permissions before tool execution
4. Handle tool errors and implement recovery strategies
5. Chain multiple tools for complex operations
6. Monitor tool performance and reliability
7. Maintain tool usage statistics"""
    
    async def initialize(self) -> None:
        """Initialize the tool agent."""
        logger.info(f"Initializing Tool Agent: {self.agent_id}")
        await self._register_default_tools()
    
    async def shutdown(self) -> None:
        """Shutdown the tool agent."""
        logger.info(f"Shutting down Tool Agent: {self.agent_id}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a tool task."""
        logger.info(f"Tool Agent executing task: {task.id}")
        
        try:
            tool_task_type = task.input_data.get("task_type", "execute")
            
            if tool_task_type == "execute":
                return await self._execute_tool(task)
            elif tool_task_type == "select":
                return await self._select_tool(task)
            elif tool_task_type == "validate_permissions":
                return await self._validate_permissions(task)
            elif tool_task_type == "chain":
                return await self._chain_tools(task)
            elif tool_task_type == "register":
                return await self._register_tool(task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown tool task type: {tool_task_type}"
                )
        
        except Exception as e:
            logger.error(f"Tool Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _execute_tool(self, task: Task) -> AgentResponse:
        """Execute a specific tool."""
        tool_name = task.input_data.get("tool_name", "")
        parameters = task.input_data.get("parameters", {})
        user_id = task.input_data.get("user_id", "")
        
        logger.info(f"Executing tool: {tool_name}")
        
        # Validate tool exists
        if tool_name not in self.tool_registry:
            return AgentResponse(
                success=False,
                error=f"Tool not found: {tool_name}"
            )
        
        # Validate permissions
        if not await self._check_permissions(tool_name, user_id):
            return AgentResponse(
                success=False,
                error=f"Permission denied for tool: {tool_name}"
            )
        
        # Get tool implementation
        tool_info = self.tool_registry[tool_name]
        tool_func = tool_info.get("function")
        
        if not tool_func:
            return AgentResponse(
                success=False,
                error=f"Tool function not implemented: {tool_name}"
            )
        
        # Execute tool with retry
        from .retry_policy import with_retry, DEFAULT_RETRY_CONFIG
        
        @with_retry(DEFAULT_RETRY_CONFIG)
        async def execute_with_retry() -> Any:
            return await tool_func(**parameters)
        
        try:
            result = await execute_with_retry()
            
            return AgentResponse(
                success=True,
                data={
                    "tool_name": tool_name,
                    "result": result,
                    "parameters": parameters
                }
            )
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            
            # Attempt error recovery
            recovery_result = await self._attempt_error_recovery(tool_name, parameters, e)
            
            if recovery_result:
                return AgentResponse(
                    success=True,
                    data={
                        "tool_name": tool_name,
                        "result": recovery_result,
                        "recovered": True,
                        "original_error": str(e)
                    }
                )
            
            return AgentResponse(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    async def _select_tool(self, task: Task) -> AgentResponse:
        """Select appropriate tool for a task."""
        task_description = task.input_data.get("task_description", "")
        available_tools = list(self.tool_registry.keys())
        
        logger.info(f"Selecting tool for task: {task_description}")
        
        # Use AI to select appropriate tool
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Task: {task_description}

Available Tools:
{self._format_tool_descriptions(available_tools)}

Select the most appropriate tool for this task. If multiple tools are needed, return them in priority order.
Output as JSON with tool names and reasoning."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        import json
        try:
            selection = json.loads(response.content)
        except (json.JSONDecodeError, ValueError):
            selection = {"tool": available_tools[0] if available_tools else None, "reasoning": response.content}
        
        return AgentResponse(
            success=True,
            data={
                "selection": selection,
                "available_tools": available_tools
            }
        )
    
    async def _validate_permissions(self, task: Task) -> AgentResponse:
        """Validate permissions for tool execution."""
        tool_name = task.input_data.get("tool_name", "")
        user_id = task.input_data.get("user_id", "")
        
        has_permission = await self._check_permissions(tool_name, user_id)
        
        return AgentResponse(
            success=True,
            data={
                "tool_name": tool_name,
                "user_id": user_id,
                "has_permission": has_permission,
                "required_permissions": self.tool_permissions.get(tool_name, [])
            }
        )
    
    async def _chain_tools(self, task: Task) -> AgentResponse:
        """Chain multiple tools for complex operations."""
        tool_chain = task.input_data.get("tool_chain", [])
        initial_data = task.input_data.get("initial_data", {})
        
        logger.info(f"Executing tool chain with {len(tool_chain)} tools")
        
        results = []
        current_data = initial_data
        
        for tool_step in tool_chain:
            tool_name = tool_step.get("tool_name")
            parameters = tool_step.get("parameters", {})
            output_mapping = tool_step.get("output_mapping", {})
            
            # Merge current data with parameters
            execution_parameters = {**parameters, **current_data}
            
            # Execute tool
            tool_task = Task(
                task_type="execute",
                description=f"Execute tool: {tool_name}",
                input_data={
                    "tool_name": tool_name,
                    "parameters": execution_parameters,
                    "user_id": task.input_data.get("user_id", "")
                },
                agent_role=AgentRole.TOOL
            )
            
            result = await self._execute_tool(tool_task)
            
            if not result.success:
                return AgentResponse(
                    success=False,
                    error=f"Tool chain failed at {tool_name}: {result.error}"
                )
            
            # Map output for next step
            for key, source_key in output_mapping.items():
                if result.data and result.data.get("result") and source_key in result.data.get("result", {}):
                    current_data[key] = result.data["result"][source_key]
            
            results.append({
                "tool_name": tool_name,
                "result": result.data.get("result") if result.data else None
            })
        
        return AgentResponse(
            success=True,
            data={
                "chain_results": results,
                "final_data": current_data
            }
        )
    
    async def _register_tool(self, task: Task) -> AgentResponse:
        """Register a new tool."""
        tool_name = task.input_data.get("tool_name", "")
        tool_description = task.input_data.get("description", "")
        tool_permissions = task.input_data.get("permissions", [])
        tool_function = task.input_data.get("function")
        
        logger.info(f"Registering tool: {tool_name}")
        
        self.tool_registry[tool_name] = {
            "description": tool_description,
            "function": tool_function,
            "registered_at": datetime.utcnow()
        }
        
        self.tool_permissions[tool_name] = tool_permissions
        
        return AgentResponse(
            success=True,
            data={
                "tool_name": tool_name,
                "description": tool_description,
                "permissions": tool_permissions
            }
        )
    
    async def _register_default_tools(self) -> None:
        """Register default tools."""
        # In real implementation, register actual tool functions
        default_tools = [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "permissions": ["internet_access"]
            },
            {
                "name": "file_read",
                "description": "Read file contents",
                "permissions": ["file_system_access"]
            },
            {
                "name": "file_write",
                "description": "Write content to file",
                "permissions": ["file_system_write"]
            },
            {
                "name": "api_call",
                "description": "Make HTTP API calls",
                "permissions": ["network_access"]
            },
            {
                "name": "code_execute",
                "description": "Execute code in sandbox",
                "permissions": ["code_execution"]
            }
        ]
        
        for tool in default_tools:
            tool_name = str(tool["name"])
            self.tool_registry[tool_name] = {
                "description": tool["description"],
                "function": None,  # Would be actual function
                "registered_at": datetime.utcnow()
            }
            self.tool_permissions[tool_name] = list(tool["permissions"])
        
        logger.info(f"Registered {len(default_tools)} default tools")
    
    async def _check_permissions(self, tool_name: str, user_id: str) -> bool:
        """Check if user has permission to use tool."""
        # In real implementation, check user permissions from database
        required_permissions = self.tool_permissions.get(tool_name, [])
        
        # For now, allow all (implement proper permission checking)
        return True
    
    async def _attempt_error_recovery(self, tool_name: str, parameters: Dict[str, Any], error: Exception) -> Optional[Any]:
        """Attempt to recover from tool execution error."""
        logger.info(f"Attempting error recovery for tool: {tool_name}")
        
        # Use AI to suggest recovery strategy
        messages = [
            Message(
                role="system",
                content="Suggest error recovery strategies for failed tool execution."
            ),
            Message(
                role="user",
                content=f"""Tool: {tool_name}
Parameters: {parameters}
Error: {error}

Suggest a recovery strategy or alternative approach."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        # In real implementation, attempt the suggested recovery
        logger.info(f"Recovery suggestion: {response.content}")
        return None
    
    def _format_tool_descriptions(self, tool_names: List[str]) -> str:
        """Format tool descriptions for AI."""
        descriptions = []
        for name in tool_names:
            info = self.tool_registry.get(name, {})
            descriptions.append(f"- {name}: {info.get('description', 'No description')}")
        return "\n".join(descriptions)
    
    def get_capabilities(self) -> List[str]:
        """Return tool agent capabilities."""
        return [
            "tool_selection",
            "tool_execution",
            "permission_validation",
            "tool_chaining",
            "error_recovery",
            "tool_registration",
            "performance_monitoring"
        ]
