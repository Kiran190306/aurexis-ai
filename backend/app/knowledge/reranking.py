"""
Reranking System
Cross encoder, context optimization, duplicate removal, result diversification
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

from loguru import logger

from app.knowledge.search import HybridSearchResult


@dataclass
class RerankedResult:
    """Reranked search result"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    original_score: float
    metadata: Dict[str, Any]
    document_title: Optional[str] = None
    document_uuid: Optional[str] = None
    rerank_reason: Optional[str] = None


class BaseReranker(ABC):
    """Base class for rerankers"""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: List[HybridSearchResult],
        top_k: int = 10
    ) -> List[RerankedResult]:
        """
        Rerank search results
        
        Args:
            query: Original search query
            results: Search results to rerank
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        pass


class CrossEncoderReranker(BaseReranker):
    """
    Cross-encoder reranking using BAAI bge-reranker or Cohere
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        self.model_name = model_name
        self.model = None
    
    def _load_model(self) -> None:
        """Load cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            logger.info(f"Loaded cross-encoder model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            self.model = None
    
    async def rerank(
        self,
        query: str,
        results: List[HybridSearchResult],
        top_k: int = 10
    ) -> List[RerankedResult]:
        """Rerank using cross-encoder"""
        if not self.model:
            logger.warning("Cross-encoder model not loaded, returning original results")
            return self._convert_to_reranked(results)
        
        if not results:
            return []
        
        # Prepare query-document pairs
        pairs = [[query, result.content] for result in results]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Combine with original scores
        reranked = []
        for result, score in zip(results, scores):
            combined_score = 0.7 * score + 0.3 * result.score
            reranked.append(RerankedResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                score=combined_score,
                original_score=result.score,
                metadata=result.metadata,
                document_title=result.document_title,
                document_uuid=result.document_uuid,
                rerank_reason="cross_encoder"
            ))
        
        # Sort by new score
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Cross-encoder reranked {len(results)} results")
        return reranked[:top_k]
    
    def _convert_to_reranked(self, results: List[HybridSearchResult]) -> List[RerankedResult]:
        """Convert to RerankedResult without reranking"""
        return [
            RerankedResult(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                content=r.content,
                score=r.score,
                original_score=r.score,
                metadata=r.metadata,
                document_title=r.document_title,
                document_uuid=r.document_uuid,
                rerank_reason="no_rerank"
            )
            for r in results
        ]


class CohereReranker(BaseReranker):
    """
    Cohere Rerank API
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "rerank-english-v2.0"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self._load_client()
    
    def _load_client(self) -> None:
        """Load Cohere client"""
        try:
            import cohere
            self.client = cohere.Client(self.api_key)
            logger.info("Cohere reranker client loaded")
        except Exception as e:
            logger.error(f"Failed to load Cohere client: {e}")
            self.client = None
    
    async def rerank(
        self,
        query: str,
        results: List[HybridSearchResult],
        top_k: int = 10
    ) -> List[RerankedResult]:
        """Rerank using Cohere API"""
        if not self.client:
            logger.warning("Cohere client not loaded, returning original results")
            return self._convert_to_reranked(results)
        
        if not results:
            return []
        
        try:
            # Prepare documents
            documents = [result.content for result in results]
            
            # Call Cohere rerank API
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=top_k
            )
            
            # Map results back
            reranked = []
            for item in response.results:
                original_result = results[item.index]
                reranked.append(RerankedResult(
                    chunk_id=original_result.chunk_id,
                    document_id=original_result.document_id,
                    content=original_result.content,
                    score=item.relevance_score,
                    original_score=original_result.score,
                    metadata=original_result.metadata,
                    document_title=original_result.document_title,
                    document_uuid=original_result.document_uuid,
                    rerank_reason="cohere_rerank"
                ))
            
            logger.info(f"Cohere reranked {len(reranked)} results")
            return reranked
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {e}")
            return self._convert_to_reranked(results)
    
    def _convert_to_reranked(self, results: List[HybridSearchResult]) -> List[RerankedResult]:
        """Convert to RerankedResult without reranking"""
        return [
            RerankedResult(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                content=r.content,
                score=r.score,
                original_score=r.score,
                metadata=r.metadata,
                document_title=r.document_title,
                document_uuid=r.document_uuid,
                rerank_reason="no_rerank"
            )
            for r in results
        ]


class ContextOptimizer:
    """
    Optimize context for LLM by removing redundancy and improving density
    """
    
    def __init__(self, redundancy_threshold: float = 0.8):
        self.redundancy_threshold = redundancy_threshold
    
    def optimize(
        self,
        results: List[RerankedResult],
        max_tokens: int = 4000
    ) -> List[RerankedResult]:
        """
        Optimize context by removing redundant content
        
        Args:
            results: Reranked results
            max_tokens: Maximum tokens to include
            
        Returns:
            Optimized results
        """
        if not results:
            return results
        
        # Remove near-duplicates
        deduplicated = self._remove_duplicates(results)
        
        # Optimize for token budget
        optimized = self._apply_token_budget(deduplicated, max_tokens)
        
        logger.info(f"Context optimization: {len(results)} -> {len(optimized)} results")
        return optimized
    
    def _remove_duplicates(
        self,
        results: List[RerankedResult]
    ) -> List[RerankedResult]:
        """Remove near-duplicate results"""
        unique_results = []
        seen_hashes = set()
        
        for result in results:
            # Simple hash-based deduplication
            content_hash = hash(result.content)
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _apply_token_budget(
        self,
        results: List[RerankedResult],
        max_tokens: int
    ) -> List[RerankedResult]:
        """Apply token budget constraint"""
        total_tokens = 0
        budgeted_results = []
        
        for result in results:
            # Estimate tokens (rough estimate: 1 token ≈ 4 characters)
            tokens = len(result.content) // 4
            
            if total_tokens + tokens <= max_tokens:
                budgeted_results.append(result)
                total_tokens += tokens
            else:
                break
        
        return budgeted_results
    
    def calculate_redundancy(self, text1: str, text2: str) -> float:
        """
        Calculate redundancy between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Redundancy score between 0 and 1
        """
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


class ResultDiversifier:
    """
    Diversify search results using Maximal Marginal Relevance (MMR)
    """
    
    def __init__(self, lambda_param: float = 0.5):
        """
        Args:
            lambda_param: Balance between relevance and diversity (0 = diversity, 1 = relevance)
        """
        self.lambda_param = lambda_param
    
    def diversify(
        self,
        results: List[RerankedResult],
        top_k: int = 10
    ) -> List[RerankedResult]:
        """
        Diversify results using MMR
        
        Args:
            results: Reranked results
            top_k: Number of results to return
            
        Returns:
            Diversified results
        """
        if not results or len(results) <= top_k:
            return results
        
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(results)
        
        # MMR algorithm
        selected = []
        remaining = list(range(len(results)))
        
        # Select first result (highest score)
        first_idx = 0
        selected.append(first_idx)
        remaining.remove(first_idx)
        
        # Select remaining results using MMR
        while len(selected) < top_k and remaining:
            best_idx = None
            best_mmr = -float('inf')
            
            for idx in remaining:
                # Calculate MMR score
                relevance = results[idx].score
                
                # Max similarity to selected
                max_sim: float = 0.0
                for sel_idx in selected:
                    sim = similarity_matrix[idx][sel_idx]
                    max_sim = max(max_sim, float(sim))
                
                # MMR = λ * relevance - (1-λ) * max_similarity
                mmr = self.lambda_param * relevance - (1 - self.lambda_param) * max_sim
                
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = idx
            
            if best_idx is not None:
                selected.append(best_idx)
                remaining.remove(best_idx)
        
        diversified = [results[idx] for idx in selected]
        logger.info(f"Diversified results: {len(diversified)} selected")
        return diversified
    
    def _calculate_similarity_matrix(
        self,
        results: List[RerankedResult]
    ) -> np.ndarray:
        """Calculate similarity matrix between results"""
        n = len(results)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._calculate_similarity(results[i].content, results[j].content)
                similarity_matrix[i, j] = sim  # type: ignore
                similarity_matrix[j, i] = sim  # type: ignore
        
        return similarity_matrix
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class RerankingPipeline:
    """
    Main reranking pipeline
    """
    
    def __init__(
        self,
        reranker: Optional[BaseReranker] = None,
        optimize_context: bool = True,
        diversify_results: bool = True
    ):
        self.reranker = reranker or CrossEncoderReranker()
        self.context_optimizer = ContextOptimizer() if optimize_context else None
        self.result_diversifier = ResultDiversifier() if diversify_results else None
    
    async def rerank(
        self,
        query: str,
        results: List[HybridSearchResult],
        top_k: int = 10,
        max_tokens: int = 4000
    ) -> List[RerankedResult]:
        """
        Complete reranking pipeline
        
        Args:
            query: Search query
            results: Search results
            top_k: Number of results to return
            max_tokens: Maximum tokens for context
            
        Returns:
            Reranked and optimized results
        """
        if not results:
            return []
        
        # Step 1: Cross-encoder reranking
        reranked = await self.reranker.rerank(query, results, top_k * 2)
        
        # Step 2: Context optimization (remove redundancy)
        if self.context_optimizer:
            reranked = self.context_optimizer.optimize(reranked, max_tokens)
        
        # Step 3: Diversify results
        if self.result_diversifier:
            reranked = self.result_diversifier.diversify(reranked, top_k)
        
        # Limit to top_k
        reranked = reranked[:top_k]
        
        logger.info(f"Reranking pipeline: {len(results)} -> {len(reranked)} results")
        return reranked


# Singleton instance (lazy-loaded)
_reranking_pipeline: Optional[RerankingPipeline] = None

def get_reranking_pipeline() -> RerankingPipeline:
    """Get or create the reranking pipeline singleton"""
    global _reranking_pipeline
    if _reranking_pipeline is None:
        _reranking_pipeline = RerankingPipeline()
    return _reranking_pipeline

# Backwards compatibility - use get_reranking_pipeline() instead
reranking_pipeline = None  # Will be initialized on first access
