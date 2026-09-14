"""
Memory Agent - Handles long-term memory, short-term memory, context retrieval, and memory management.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from app.ai.engine import ai_engine
from app.ai.base import Message
from .base import BaseAgent, AgentRole, Task, AgentResponse


class MemoryAgent(BaseAgent):
    """Agent responsible for memory management and retrieval."""
    
    def __init__(self, agent_id: str = "memory", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.role = AgentRole.MEMORY
        self.short_term_memory: List[Dict[str, Any]] = []
        self.long_term_memory_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self.max_short_term_items = 100
        self.system_prompt = """You are a Memory Agent for Jarvis AI. Your role is to:
1. Store and retrieve information from long-term memory
2. Manage short-term working memory for current context
3. Compress and summarize old memories to save space
4. Retrieve relevant context based on queries
5. Identify important information to remember long-term
6. Synthesize related memories for context"""
    
    async def initialize(self) -> None:
        """Initialize the memory agent."""
        logger.info(f"Initializing Memory Agent: {self.agent_id}")
        # Initialize memory storage connections
    
    async def shutdown(self) -> None:
        """Shutdown the memory agent."""
        logger.info(f"Shutting down Memory Agent: {self.agent_id}")
        # Cleanup and persist memory
    
    async def execute(self, task: Task) -> AgentResponse:
        """Execute a memory task."""
        logger.info(f"Memory Agent executing task: {task.id}")
        
        try:
            memory_task_type = task.input_data.get("task_type", "retrieve")
            
            if memory_task_type == "store":
                return await self._store_memory(task)
            elif memory_task_type == "retrieve":
                return await self._retrieve_memory(task)
            elif memory_task_type == "search":
                return await self._search_memory(task)
            elif memory_task_type == "compress":
                return await self._compress_memory(task)
            elif memory_task_type == "summarize":
                return await self._summarize_memory(task)
            elif memory_task_type == "context":
                return await self._get_context(task)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown memory task type: {memory_task_type}"
                )
        
        except Exception as e:
            logger.error(f"Memory Agent execution failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e)
            )
    
    async def _store_memory(self, task: Task) -> AgentResponse:
        """Store information in memory."""
        content = task.input_data.get("content", "")
        memory_type = task.input_data.get("memory_type", "episodic")
        importance = task.input_data.get("importance", 0.5)
        tags = task.input_data.get("tags", [])
        
        logger.info(f"Storing {memory_type} memory with importance {importance}")
        
        # Determine storage based on importance and type
        if importance > 0.7 or memory_type == "semantic":
            # Store in long-term memory
            memory_id = await self._store_long_term(content, memory_type, importance, tags)
        else:
            # Store in short-term memory
            memory_id = await self._store_short_term(content, memory_type, importance, tags)
        
        return AgentResponse(
            success=True,
            data={
                "memory_id": memory_id,
                "memory_type": memory_type,
                "importance": importance
            }
        )
    
    async def _retrieve_memory(self, task: Task) -> AgentResponse:
        """Retrieve specific memory by ID."""
        memory_id = task.input_data.get("memory_id", "")
        
        logger.info(f"Retrieving memory: {memory_id}")
        
        # Check short-term memory first
        for memory in self.short_term_memory:
            if memory.get("id") == memory_id:
                return AgentResponse(
                    success=True,
                    data={"memory": memory, "source": "short_term"}
                )
        
        # Check long-term memory cache
        if memory_id in self.long_term_memory_cache:
            return AgentResponse(
                success=True,
                data={"memory": self.long_term_memory_cache[memory_id], "source": "long_term"}
            )
        
        # Fetch from database if not in cache
        db_memory: Optional[Dict[str, Any]] = await self._fetch_from_database(memory_id)
        if db_memory:
            self.long_term_memory_cache[memory_id] = db_memory
            return AgentResponse(
                success=True,
                data={"memory": db_memory, "source": "database"}
            )
        
        return AgentResponse(
            success=False,
            error=f"Memory not found: {memory_id}"
        )
    
    async def _search_memory(self, task: Task) -> AgentResponse:
        """Search memory by query."""
        query = task.input_data.get("query", "")
        memory_type = task.input_data.get("memory_type", None)
        limit = task.input_data.get("limit", 10)
        
        logger.info(f"Searching memory for: {query}")
        
        # Use AI to understand query and generate search terms
        search_terms = await self._generate_search_terms(query)
        
        # Search both short-term and long-term memory
        results = []
        
        # Search short-term memory
        for memory in self.short_term_memory:
            if self._memory_matches_query(memory, search_terms):
                if not memory_type or memory.get("type") == memory_type:
                    results.append(memory)
        
        # Search long-term memory (simplified - in real implementation, use vector search)
        long_term_results = await self._search_long_term_memory(search_terms, memory_type, limit)
        results.extend(long_term_results)
        
        # Rank results by relevance
        ranked_results = await self._rank_search_results(results, query)
        
        return AgentResponse(
            success=True,
            data={
                "query": query,
                "results": ranked_results[:limit],
                "total_found": len(ranked_results)
            }
        )
    
    async def _compress_memory(self, task: Task) -> AgentResponse:
        """Compress old memories to save space."""
        memory_ids = task.input_data.get("memory_ids", [])
        compression_ratio = task.input_data.get("compression_ratio", 0.5)
        
        logger.info(f"Compressing {len(memory_ids)} memories")
        
        compressed_memories = []
        for memory_id in memory_ids:
            memory = await self._fetch_memory(memory_id)
            if memory:
                compressed = await self._compress_single_memory(memory, compression_ratio)
                compressed_memories.append(compressed)
        
        return AgentResponse(
            success=True,
            data={
                "compressed_memories": compressed_memories,
                "original_count": len(memory_ids),
                "compression_ratio": compression_ratio
            }
        )
    
    async def _summarize_memory(self, task: Task) -> AgentResponse:
        """Summarize a set of memories."""
        memory_ids = task.input_data.get("memory_ids", [])
        summary_type = task.input_data.get("summary_type", "comprehensive")
        
        logger.info(f"Summarizing {len(memory_ids)} memories")
        
        memories = []
        for memory_id in memory_ids:
            memory = await self._fetch_memory(memory_id)
            if memory:
                memories.append(memory)
        
        summary = await self._generate_summary(memories, summary_type)
        
        return AgentResponse(
            success=True,
            data={
                "summary": summary,
                "memory_count": len(memories),
                "summary_type": summary_type
            }
        )
    
    async def _get_context(self, task: Task) -> AgentResponse:
        """Get relevant context for a query."""
        query = task.input_data.get("query", "")
        context_window = task.input_data.get("context_window", 5)
        
        logger.info(f"Getting context for: {query}")
        
        # Search for relevant memories
        search_result = await self._search_memory(Task(
            task_type="search",
            description="Search memory for context",
            input_data={"query": query, "limit": context_window * 2},
            agent_role=AgentRole.MEMORY
        ))
        
        if not search_result.success:
            return AgentResponse(
                success=False,
                error="Failed to search for context"
            )
        
        # Use AI to synthesize context
        memories = search_result.data.get("results", []) if search_result.data else []
        context = await self._synthesize_context(memories, query)
        
        return AgentResponse(
            success=True,
            data={
                "context": context,
                "source_memories": len(memories)
            }
        )
    
    async def _store_long_term(self, content: str, memory_type: str, importance: float, tags: List[str]) -> str:
        """Store in long-term memory (database)."""
        # In real implementation, store in database
        import uuid
        memory_id = str(uuid.uuid4())
        self.long_term_memory_cache[memory_id] = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "importance": importance,
            "tags": tags
        }
        return memory_id
    
    async def _store_short_term(self, content: str, memory_type: str, importance: float, tags: List[str]) -> str:
        """Store in short-term memory."""
        import uuid
        memory_id = str(uuid.uuid4())
        
        self.short_term_memory.append({
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "importance": importance,
            "tags": tags,
            "timestamp": datetime.utcnow()
        })
        
        # Maintain max size
        if len(self.short_term_memory) > self.max_short_term_items:
            self.short_term_memory.pop(0)
        
        return memory_id
    
    async def _fetch_from_database(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Fetch memory from database."""
        # In real implementation, fetch from database
        return None
    
    async def _fetch_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Fetch memory from any source."""
        # Check short-term
        for memory in self.short_term_memory:
            if memory.get("id") == memory_id:
                return memory
        
        # Check cache
        if memory_id in self.long_term_memory_cache:
            return self.long_term_memory_cache[memory_id]
        
        # Fetch from database
        return await self._fetch_from_database(memory_id)
    
    async def _generate_search_terms(self, query: str) -> List[str]:
        """Generate search terms from query using AI."""
        messages = [
            Message(
                role="system",
                content="Extract key search terms from a query for memory search."
            ),
            Message(
                role="user",
                content=f"Query: {query}\n\nExtract 5-10 key search terms as a JSON array."
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=200
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

            return json.loads(response_content)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, ValueError):
            return query.split()
    
    def _memory_matches_query(self, memory: Dict[str, Any], search_terms: List[str]) -> bool:
        """Check if memory matches search terms."""
        content = memory.get("content", "").lower()
        return any(term.lower() in content for term in search_terms)
    
    async def _search_long_term_memory(self, search_terms: List[str], memory_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Search long-term memory."""
        # In real implementation, use vector search
        return []
    
    async def _rank_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance."""
        # Use AI to rank results
        if not results:
            return []
        
        messages = [
            Message(
                role="system",
                content="Rank search results by relevance to the query."
            ),
            Message(
                role="user",
                content=f"""Query: {query}

Results: {results}

Return ranked results as JSON array."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
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

            return json.loads(response_content)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, ValueError):
            return results
    
    async def _compress_single_memory(self, memory: Dict[str, Any], compression_ratio: float) -> Dict[str, Any]:
        """Compress a single memory."""
        messages = [
            Message(
                role="system",
                content="Compress and summarize the memory while retaining key information."
            ),
            Message(
                role="user",
                content=f"""Memory: {memory}

Compress to {compression_ratio * 100}% of original length while retaining key information."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        return {
            **memory,
            "content": response.content,
            "compressed": True
        }
    
    async def _generate_summary(self, memories: List[Dict[str, Any]], summary_type: str) -> str:
        """Generate summary of memories."""
        messages = [
            Message(
                role="system",
                content=f"Generate a {summary_type} summary of the provided memories."
            ),
            Message(
                role="user",
                content=f"""Memories: {memories}

Generate a {summary_type} summary."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )
        
        return response.content
    
    async def _synthesize_context(self, memories: List[Dict[str, Any]], query: str) -> str:
        """Synthesize context from memories."""
        messages = [
            Message(
                role="system",
                content="Synthesize relevant context from memories for a query."
            ),
            Message(
                role="user",
                content=f"""Query: {query}

Relevant Memories: {memories}

Synthesize a concise context paragraph that provides relevant background information."""
            )
        ]
        
        response = await ai_engine.generate(
            messages=messages,
            temperature=0.5,
            max_tokens=1000
        )
        
        return response.content
    
    def get_capabilities(self) -> List[str]:
        """Return memory agent capabilities."""
        return [
            "memory_storage",
            "memory_retrieval",
            "memory_search",
            "memory_compression",
            "memory_summarization",
            "context_retrieval",
            "short_term_memory",
            "long_term_memory"
        ]
