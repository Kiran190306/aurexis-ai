import httpx
from typing import Any
from .base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from loguru import logger


class WebSearchTool(BaseTool):
    """Tool for searching the web"""
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="Search the web for information using a search engine",
            category="search",
            parameters={
                "query": ToolParameter(
                    name="query",
                    type="string",
                    description="The search query",
                    required=True
                ),
                "num_results": ToolParameter(
                    name="num_results",
                    type="integer",
                    description="Number of results to return",
                    required=False,
                    default=5
                )
            }
        )
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        import time
        start_time = time.time()
        
        query = kwargs.get("query")
        num_results = kwargs.get("num_results", 5)
        
        if not query:
            return ToolResult(
                success=False,
                error="Query parameter is required"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Using DuckDuckGo as a simple example (no API key required)
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Extract related topics as results
                    if "RelatedTopics" in data:
                        for topic in data["RelatedTopics"][:num_results]:
                            if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                                results.append({
                                    "title": topic.get("Text", ""),
                                    "url": topic.get("FirstURL", ""),
                                    "snippet": topic.get("Text", "")
                                })
                    
                    execution_time = time.time() - start_time
                    return ToolResult(
                        success=True,
                        data={"results": results, "query": query},
                        execution_time=execution_time
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"Search failed with status {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
