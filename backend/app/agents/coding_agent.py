"""
Coding Agent - Handles code generation, refactoring, debugging, and testing.
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from .base import BaseAgent, AgentRole, Task, AgentResponse


class CodingAgent(BaseAgent):
    """Agent responsible for code-related tasks."""
    
    def __init__(self, agent_id: str = "coding", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.CODING
        self.system_prompt = """You are a Coding Agent for Jarvis AI. Your role is to:
1. Generate clean, efficient, and well-documented code
2. Refactor existing code for better performance and readability
3. Debug code issues and provide fixes
4. Generate comprehensive unit and integration tests
5. Review code for best practices and security issues
6. Generate documentation and comments
7. Follow language-specific best practices and conventions"""
    
    async def initialize(self) -> None:
        """Initialize the coding agent."""
        logger.info(f"Initializing Coding Agent: {self.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the coding agent."""
        logger.info(f"Shutting down Coding Agent: {self.agent_id}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a coding task."""
        logger.info(f"Coding Agent executing task: {task.id}")
        
        try:
            coding_task_type = task.input_data.get("task_type", "generation")
            
            if coding_task_type == "generation":
                return await self._code_generation(task)
            elif coding_task_type == "refactoring":
                return await self._code_refactoring(task)
            elif coding_task_type == "debugging":
                return await self._code_debugging(task)
            elif coding_task_type == "testing":
                return await self._test_generation(task)
            elif coding_task_type == "review":
                return await self._code_review(task)
            elif coding_task_type == "documentation":
                return await self._documentation_generation(task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown coding task type: {coding_task_type}"
                )
        
        except Exception as e:
            logger.error(f"Coding Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _code_generation(self, task: Task) -> AgentResponse:
        """Generate code from requirements."""
        requirements = task.input_data.get("requirements", "")
        language = task.input_data.get("language", "python")
        context = task.input_data.get("context", {})
        
        logger.info(f"Generating {language} code")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Language: {language}

Requirements: {requirements}

Context: {context}

Please generate clean, efficient, and well-documented code that meets these requirements.
Include:
1. The complete implementation
2. Inline comments for complex logic
3. Error handling
4. Type hints where applicable
5. Example usage if helpful

Output only the code with minimal explanation."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=4000
        )
        
        return AgentResponse(
            success=True,
            data={
                "language": language,
                "code": response.content,
                "requirements": requirements
            }
        )
    
    async def _code_refactoring(self, task: Task) -> AgentResponse:
        """Refactor existing code."""
        code = task.input_data.get("code", "")
        refactoring_goals = task.input_data.get("goals", ["performance", "readability"])
        
        logger.info("Refactoring code")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Code to refactor:
{code}

Refactoring goals: {refactoring_goals}

Please refactor the code to improve:
1. Performance
2. Readability
3. Maintainability
4. Error handling

Provide the refactored code with explanations of changes made."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=4000
        )
        
        return AgentResponse(
            success=True,
            data={
                "original_code": code,
                "refactored_code": response.content,
                "goals": refactoring_goals
            }
        )
    
    async def _code_debugging(self, task: Task) -> AgentResponse:
        """Debug code issues."""
        code = task.input_data.get("code", "")
        error_message = task.input_data.get("error", "")
        description = task.input_data.get("description", "")
        
        logger.info(f"Debugging code: {error_message}")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Code:
{code}

Error: {error_message}

Description: {description}

Please:
1. Identify the root cause of the error
2. Provide a fix
3. Explain the issue
4. Suggest how to prevent similar issues"""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=3000
        )
        
        return AgentResponse(
            success=True,
            data={
                "error": error_message,
                "diagnosis": response.content,
                "fixed_code": self._extract_fixed_code(response.content)
            }
        )
    
    async def _test_generation(self, task: Task) -> AgentResponse:
        """Generate tests for code."""
        code = task.input_data.get("code", "")
        test_framework = task.input_data.get("framework", "pytest")
        test_type = task.input_data.get("test_type", "unit")
        
        logger.info(f"Generating {test_type} tests using {test_framework}")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Code to test:
{code}

Test Framework: {test_framework}
Test Type: {test_type}

Please generate comprehensive tests that:
1. Cover happy path scenarios
2. Test edge cases
3. Include error handling tests
4. Use appropriate assertions
5. Include setup/teardown if needed"""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=3000
        )
        
        return AgentResponse(
            success=True,
            data={
                "test_code": response.content,
                "framework": test_framework,
                "test_type": test_type
            }
        )
    
    async def _code_review(self, task: Task) -> AgentResponse:
        """Review code for issues and improvements."""
        code = task.input_data.get("code", "")
        review_criteria = task.input_data.get("criteria", ["security", "performance", "best_practices"])
        
        logger.info("Reviewing code")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Code to review:
{code}

Review criteria: {review_criteria}

Please provide a comprehensive review covering:
1. Security vulnerabilities
2. Performance issues
3. Code style and best practices
4. Potential bugs
5. Suggestions for improvement

Format the review with clear sections and severity levels."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=3000
        )
        
        return AgentResponse(
            success=True,
            data={
                "review": response.content,
                "criteria": review_criteria
            }
        )
    
    async def _documentation_generation(self, task: Task) -> AgentResponse:
        """Generate documentation for code."""
        code = task.input_data.get("code", "")
        doc_type = task.input_data.get("doc_type", "docstring")
        
        logger.info(f"Generating {doc_type} documentation")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Code:
{code}

Documentation type: {doc_type}

Please generate appropriate documentation that:
1. Explains the purpose and functionality
2. Documents parameters and return values
3. Includes usage examples
4. Notes any important considerations
5. Follows standard documentation formats"""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        return AgentResponse(
            success=True,
            data={
                "documentation": response.content,
                "doc_type": doc_type
            }
        )
    
    def _extract_fixed_code(self, response: str) -> str:
        """Extract fixed code from debugging response."""
        # Simple extraction - in real implementation, use proper parsing
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def get_capabilities(self) -> List[str]:
        """Return coding agent capabilities."""
        return [
            "code_generation",
            "code_refactoring",
            "debugging",
            "test_generation",
            "code_review",
            "documentation_generation",
            "security_analysis"
        ]
