"""
Reflection Agent - Evaluates responses, detects hallucinations, verifies reasoning, and suggests improvements.
Integrates with Knowledge Agent for RAG response verification.
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from .base import BaseAgent, AgentRole, Task, AgentResponse
from app.knowledge.agent import KnowledgeAgent, RAGQuery


class ReflectionAgent(BaseAgent):
    """Agent responsible for reflection and quality control."""
    
    def __init__(self, agent_id: str = "reflection", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.REFLECTION
        self.quality_threshold = 0.7
        self.hallucination_threshold = 0.3
        self.knowledge_agent = KnowledgeAgent()
        self.system_prompt = """You are a Reflection Agent for Jarvis AI. Your role is to:
1. Evaluate generated responses for quality and accuracy
2. Detect potential hallucinations or factual errors
3. Verify reasoning logic and coherence
4. Identify areas for improvement
5. Suggest corrections or refinements
6. Trigger retries when quality is insufficient
7. Provide detailed feedback for agent improvement
8. Verify RAG responses against knowledge base sources"""
    
    async def initialize(self) -> None:
        """Initialize the reflection agent."""
        logger.info(f"Initializing Reflection Agent: {self.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the reflection agent."""
        logger.info(f"Shutting down Reflection Agent: {self.agent_id}")
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a reflection task."""
        logger.info(f"Reflection Agent executing task: {task.id}")
        
        try:
            reflection_task_type = task.input_data.get("task_type", "evaluate")
            
            if reflection_task_type == "evaluate":
                return await self._evaluate_response(task)
            elif reflection_task_type == "detect_hallucination":
                return await self._detect_hallucination(task)
            elif reflection_task_type == "verify_reasoning":
                return await self._verify_reasoning(task)
            elif reflection_task_type == "suggest_improvements":
                return await self._suggest_improvements(task)
            elif reflection_task_type == "quality_check":
                return await self._quality_check(task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown reflection task type: {reflection_task_type}"
                )
        
        except Exception as e:
            logger.error(f"Reflection Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _evaluate_response(self, task: Task) -> AgentResponse:
        """Evaluate a generated response for quality."""
        original_request = task.input_data.get("original_request", "")
        generated_response = task.input_data.get("generated_response", "")
        context = task.input_data.get("context", {})
        
        logger.info("Evaluating response quality")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Original Request: {original_request}

Generated Response: {generated_response}

Context: {context}

Evaluate this response on:
1. Relevance to the request
2. Accuracy and factual correctness
3. Completeness
4. Clarity and coherence
5. Tone and appropriateness

Provide a score (0-1) for each criterion and an overall quality score.
Also provide specific feedback on strengths and areas for improvement.
Output as JSON with scores and detailed feedback."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        import json
        try:
            # Safely access response content
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            evaluation = json.loads(response_content)
        except (json.JSONDecodeError, ValueError):
            evaluation = {
                "overall_score": 0.5,
                "feedback": response_content if 'response_content' in locals() else str(response)
            }
        
        overall_score = evaluation.get("overall_score", 0.5)
        quality_pass = overall_score >= self.quality_threshold
        
        return AgentResponse(
            success=True,
            data={
                "evaluation": evaluation,
                "overall_score": overall_score,
                "quality_pass": quality_pass,
                "should_retry": not quality_pass
            }
        )
    
    async def _detect_hallucination(self, task: Task) -> AgentResponse:
        """Detect potential hallucinations in the response."""
        generated_response = task.input_data.get("generated_response", "")
        knowledge_base = task.input_data.get("knowledge_base", [])
        user_id = task.input_data.get("user_id")
        original_query = task.input_data.get("original_query", "")
        
        logger.info("Detecting potential hallucinations")
        
        # Use RAG to verify claims if user_id is provided
        rag_verification = ""
        if user_id and original_query:
            try:
                rag_query = RAGQuery(
                    query=original_query,
                    user_id=user_id,
                    top_k=3,
                    use_hybrid=True,
                    max_tokens=500
                )
                rag_result = await self.knowledge_agent.query(rag_query)
                if rag_result.context.context_text:
                    rag_verification = f"\n\nKnowledge Base Verification:\n{rag_result.context.context_text}"
                    logger.info(f"RAG verification with {len(rag_result.sources)} sources")
            except Exception as e:
                logger.warning(f"RAG verification failed: {e}")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Generated Response: {generated_response}

Knowledge Base Context: {knowledge_base}{rag_verification}

Analyze this response for:
1. Factual inconsistencies
2. Claims not supported by evidence
3. Contradictions with known facts
4. Overconfident statements without basis
5. Fabricated information

Provide a hallucination probability score (0-1) and identify specific problematic statements.
Output as JSON with score and detailed analysis."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        import json
        try:
            # Safely access response content
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            analysis = json.loads(response_content)
        except (json.JSONDecodeError, ValueError):
            analysis = {
                "hallucination_probability": 0.5,
                "analysis": response_content if 'response_content' in locals() else str(response)
            }
        
        hallucination_score = analysis.get("hallucination_probability", 0.5)
        has_hallucination = hallucination_score > self.hallucination_threshold
        
        return AgentResponse(
            success=True,
            data={
                "analysis": analysis,
                "hallucination_score": hallucination_score,
                "has_hallucination": has_hallucination,
                "should_retry": has_hallucination,
                "rag_verified": bool(rag_verification)
            }
        )
    
    async def _verify_reasoning(self, task: Task) -> AgentResponse:
        """Verify the reasoning logic in the response."""
        reasoning_chain = task.input_data.get("reasoning_chain", [])
        conclusion = task.input_data.get("conclusion", "")
        
        logger.info("Verifying reasoning logic")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Reasoning Chain: {reasoning_chain}

Conclusion: {conclusion}

Verify the reasoning by checking:
1. Logical consistency between steps
2. Valid inference patterns
3. Absence of logical fallacies
4. Soundness of arguments
5. Connection between premises and conclusion

Provide a reasoning quality score (0-1) and identify any logical issues.
Output as JSON with score and detailed analysis."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        import json
        try:
            # Safely access response content
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            verification = json.loads(response_content)
        except (json.JSONDecodeError, ValueError):
            verification = {
                "reasoning_score": 0.5,
                "analysis": response_content if 'response_content' in locals() else str(response)
            }
        
        reasoning_score = verification.get("reasoning_score", 0.5)
        reasoning_valid = reasoning_score >= self.quality_threshold
        
        return AgentResponse(
            success=True,
            data={
                "verification": verification,
                "reasoning_score": reasoning_score,
                "reasoning_valid": reasoning_valid,
                "should_retry": not reasoning_valid
            }
        )
    
    async def _suggest_improvements(self, task: Task) -> AgentResponse:
        """Suggest improvements for a response."""
        generated_response = task.input_data.get("generated_response", "")
        original_request = task.input_data.get("original_request", "")
        evaluation_feedback = task.input_data.get("evaluation_feedback", {})
        
        logger.info("Suggesting improvements")
        
        messages = [
            Message(
                role="system",
                content=self.system_prompt
            ),
            Message(
                role="user",
                content=f"""Original Request: {original_request}

Generated Response: {generated_response}

Evaluation Feedback: {evaluation_feedback}

Based on the feedback, suggest specific improvements to make this response better.
Provide:
1. Concrete suggestions for improvement
2. Rewritten sections if needed
3. Additional information to include
4. Structural changes if beneficial
5. Tone adjustments if necessary

Output as JSON with detailed suggestions."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )
        
        import json
        try:
            # Safely access response content
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict):
                response_content = response.get('content', '')
            else:
                response_content = str(response)

            suggestions = json.loads(response_content)
        except (json.JSONDecodeError, ValueError):
            suggestions = {
                "suggestions": response_content if 'response_content' in locals() else str(response)
            }
        
        return AgentResponse(
            success=True,
            data={
                "suggestions": suggestions
            }
        )
    
    async def _quality_check(self, task: Task) -> AgentResponse:
        """Perform comprehensive quality check."""
        generated_response = task.input_data.get("generated_response", "")
        original_request = task.input_data.get("original_request", "")
        
        logger.info("Performing comprehensive quality check")
        
        # Run all checks
        evaluation_result = await self._evaluate_response(Task(
            task_type="evaluate",
            description="Evaluate response quality",
            input_data={
                "original_request": original_request,
                "generated_response": generated_response
            },
            agent_role=AgentRole.REFLECTION
        ))
        
        hallucination_result = await self._detect_hallucination(Task(
            task_type="detect_hallucination",
            description="Detect hallucinations in response",
            input_data={
                "generated_response": generated_response
            },
            agent_role=AgentRole.REFLECTION
        ))
        
        # Determine overall quality
        quality_pass = (
            evaluation_result.data.get("quality_pass", False) if evaluation_result.data else False and
            not (hallucination_result.data.get("has_hallucination", False) if hallucination_result.data else False)
        )
        
        return AgentResponse(
            success=True,
            data={
                "evaluation": evaluation_result.data,
                "hallucination_check": hallucination_result.data,
                "overall_quality_pass": quality_pass,
                "should_retry": not quality_pass
            }
        )
    
    def get_capabilities(self) -> List[str]:
        """Return reflection agent capabilities."""
        return [
            "response_evaluation",
            "hallucination_detection",
            "reasoning_verification",
            "improvement_suggestion",
            "quality_assurance",
            "feedback_generation"
        ]
