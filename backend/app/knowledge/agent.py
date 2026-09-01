"""
Knowledge Agent
Orchestrates retriever, reranker, and context builder for RAG
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from app.knowledge.search import HybridSearchEngine, get_hybrid_search_engine, SearchFilter
from app.knowledge.reranking import RerankingPipeline, get_reranking_pipeline
from app.knowledge.context import ContextBuilder, get_context_builder, BuiltContext
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.core.database import AsyncSessionLocal
from sqlalchemy import select


@dataclass
class RAGQuery:
    """RAG query with parameters"""
    query: str
    user_id: int
    top_k: int = 10
    use_hybrid: bool = True
    filters: Optional[Dict[str, Any]] = None
    max_tokens: int = 4000
    include_citations: bool = True


@dataclass
class RAGResult:
    """RAG result with context and metadata"""
    query: str
    context: BuiltContext
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Optional[int] = None


class KnowledgeAgent:
    """
    Knowledge Agent for RAG orchestration
    Integrates retriever, reranker, and context builder
    """
    
    def __init__(
        self,
        search_engine: Optional[HybridSearchEngine] = None,
        reranking_pipeline: Optional[RerankingPipeline] = None,
        context_builder: Optional[ContextBuilder] = None
    ):
        self.search_engine = search_engine or get_hybrid_search_engine()
        self.reranking_pipeline = reranking_pipeline or get_reranking_pipeline()
        self.context_builder = context_builder or get_context_builder()
    
    async def query(
        self,
        rag_query: RAGQuery
    ) -> RAGResult:
        """
        Execute RAG query
        
        Args:
            rag_query: RAGQuery object
            
        Returns:
            RAGResult with context and metadata
        """
        import time
        start_time = time.time()
        
        # Step 1: Get user's chunks for search
        chunks = await self._get_user_chunks(rag_query.user_id)
        
        # Step 2: Index chunks for BM25
        if chunks:
            self.search_engine.index_chunks(list(chunks))
        
        # Step 3: Build filters
        filters = rag_query.filters or {}
        filters['user_id'] = rag_query.user_id
        
        # Step 4: Search
        search_results = await self.search_engine.search(
            query=rag_query.query,
            chunks=chunks,
            top_k=rag_query.top_k * 2,  # Get more for reranking
            filters=filters,
            use_hybrid=rag_query.use_hybrid
        )
        
        # Step 4: Rerank
        reranked_results = await self.reranking_pipeline.rerank(
            query=rag_query.query,
            results=search_results,
            top_k=rag_query.top_k,
            max_tokens=rag_query.max_tokens
        )
        
        # Step 5: Build context
        built_context = self.context_builder.build_context(
            query=rag_query.query,
            results=reranked_results,
            include_citations=rag_query.include_citations
        )
        
        # Step 6: Prepare sources
        sources = self._prepare_sources(reranked_results, built_context.citations)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build result
        result = RAGResult(
            query=rag_query.query,
            context=built_context,
            sources=sources,
            metadata={
                'search_results_count': len(search_results),
                'reranked_results_count': len(reranked_results),
                'total_sources': built_context.total_sources,
                'average_confidence': built_context.average_confidence,
                'use_hybrid': rag_query.use_hybrid,
                'top_k': rag_query.top_k,
            },
            latency_ms=latency_ms
        )
        
        logger.info(
            f"RAG query completed: {rag_query.query[:50]}..., "
            f"{len(sources)} sources, {latency_ms}ms"
        )
        
        return result
    
    async def _get_user_chunks(self, user_id: int) -> List[KnowledgeChunk]:
        """Get all chunks for a user"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeChunk).join(KnowledgeDocument).where(
                    KnowledgeDocument.user_id == user_id,
                    KnowledgeDocument.deleted_at.is_(None)
                )
            )
            chunks = result.scalars().all()
            return list(chunks)
    
    def _prepare_sources(
        self,
        reranked_results: List,
        citations: List
    ) -> List[Dict[str, Any]]:
        """Prepare source information"""
        sources = []
        
        for result, citation in zip(reranked_results, citations):
            sources.append({
                'chunk_id': result.chunk_id,
                'document_id': result.document_id,
                'document_title': citation.document_title,
                'document_uuid': citation.document_uuid,
                'page_number': citation.page_number,
                'confidence': citation.confidence,
                'relevance_score': citation.relevance_score,
                'content_preview': result.content[:200] + "..." if len(result.content) > 200 else result.content
            })
        
        return sources
    
    async def query_with_answer(
        self,
        rag_query: RAGQuery,
        llm_client: Optional[Any] = None
    ) -> RAGResult:
        """
        Execute RAG query and generate answer using LLM
        
        Args:
            rag_query: RAGQuery object
            llm_client: Optional LLM client for answer generation
            
        Returns:
            RAGResult with answer
        """
        # Get context
        rag_result = await self.query(rag_query)
        
        # Generate answer if LLM client provided
        if llm_client:
            answer = await self._generate_answer(
                rag_result.context.context_text,
                rag_query.query,
                llm_client
            )
            rag_result.answer = answer
        
        return rag_result
    
    async def _generate_answer(
        self,
        context: str,
        query: str,
        llm_client: Any
    ) -> str:
        """Generate answer using LLM"""
        try:
            # Build prompt
            prompt = f"""Context:
{context}

Question: {query}

Please answer the question based on the provided context. If the context doesn't contain enough information to answer the question, please state that clearly."""
            
            # Call LLM (implementation depends on LLM client)
            response = await llm_client.generate(prompt)
            return str(response)
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "Failed to generate answer due to an error."
    
    async def multi_hop_query(
        self,
        rag_query: RAGQuery,
        max_hops: int = 3
    ) -> RAGResult:
        """
        Execute multi-hop query for complex questions
        
        Args:
            rag_query: RAGQuery object
            max_hops: Maximum number of retrieval hops
            
        Returns:
            RAGResult with accumulated context
        """
        accumulated_context = ""
        all_sources = []
        current_query = rag_query.query
        
        for hop in range(max_hops):
            # Execute query
            hop_query = RAGQuery(
                query=current_query,
                user_id=rag_query.user_id,
                top_k=rag_query.top_k,
                use_hybrid=rag_query.use_hybrid,
                filters=rag_query.filters,
                max_tokens=rag_query.max_tokens // max_hops,
                include_citations=True
            )
            
            hop_result = await self.query(hop_query)
            
            # Accumulate context
            accumulated_context += f"\n\nHop {hop + 1}:\n{hop_result.context.context_text}"
            all_sources.extend(hop_result.sources)
            
            # Stop if confidence is high
            if hop_result.context.average_confidence > 0.8:
                break
            
            # Update query for next hop (simple approach: use original query)
            current_query = rag_query.query
        
        # Build final result
        final_context = BuiltContext(
            context_text=accumulated_context.strip(),
            citations=[],  # Would need to rebuild from all_sources
            total_tokens=len(accumulated_context) // 4,
            total_sources=len(set(s['document_id'] for s in all_sources)),
            average_confidence=sum(hop_result.context.average_confidence for hop_result in [hop_result]) if 'hop_result' in locals() else 0,
            metadata={'multi_hop': True, 'hops_completed': hop + 1}
        )
        
        return RAGResult(
            query=rag_query.query,
            context=final_context,
            sources=all_sources,
            metadata={'multi_hop': True, 'hops_completed': hop + 1}
        )


class KnowledgeRetriever:
    """
    Specialized retriever component of Knowledge Agent
    """
    
    def __init__(self, search_engine: Optional[HybridSearchEngine] = None):
        self.search_engine = search_engine or get_hybrid_search_engine()
    
    async def retrieve(
        self,
        query: str,
        user_id: int,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List:
        """
        Retrieve relevant chunks
        
        Args:
            query: Search query
            user_id: User ID
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            List of search results
        """
        # Get user chunks
        chunks = await self._get_user_chunks(user_id)
        
        # Build filters
        filters = filters or {}
        filters['user_id'] = user_id
        
        # Search
        results = await self.search_engine.search(
            query=query,
            chunks=chunks,
            top_k=top_k,
            filters=filters,
            use_hybrid=True
        )
        
        return results
    
    async def _get_user_chunks(self, user_id: int) -> List[KnowledgeChunk]:
        """Get all chunks for a user"""
        async for db in get_db():
            result = await db.execute(
                select(KnowledgeChunk).join(KnowledgeDocument).where(
                    KnowledgeDocument.user_id == user_id,
                    KnowledgeDocument.deleted_at.is_(None)
                )
            )
            chunks = result.scalars().all()
            return list(chunks)
        return []


class KnowledgeReranker:
    """
    Specialized reranker component of Knowledge Agent
    """
    
    def __init__(self, reranking_pipeline: Optional[RerankingPipeline] = None):
        self.reranking_pipeline = reranking_pipeline or get_reranking_pipeline()
    
    async def rerank(
        self,
        query: str,
        results: List,
        top_k: int = 10
    ) -> List:
        """
        Rerank search results
        
        Args:
            query: Search query
            results: Search results
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        return await self.reranking_pipeline.rerank(
            query=query,
            results=results,
            top_k=top_k
        )


class KnowledgeContextBuilder:
    """
    Specialized context builder component of Knowledge Agent
    """
    
    def __init__(self, context_builder: Optional[ContextBuilder] = None):
        self.context_builder = context_builder or get_context_builder()
    
    async def build(
        self,
        query: str,
        results: List,
        max_tokens: int = 4000
    ) -> BuiltContext:
        """
        Build context from results
        
        Args:
            query: Search query
            results: Reranked results
            max_tokens: Maximum tokens
            
        Returns:
            Built context
        """
        return self.context_builder.build_context(
            query=query,
            results=results,
            include_citations=True
        )


# Singleton instance
knowledge_agent = KnowledgeAgent()
