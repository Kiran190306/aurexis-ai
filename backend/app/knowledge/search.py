"""
Hybrid Search System
BM25, dense retrieval, hybrid ranking, metadata filtering, score normalization
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

from loguru import logger

from app.knowledge.vector_store import SearchResult, BaseVectorStore, get_vector_store
from app.knowledge.embeddings import EmbeddingPipeline, embedding_pipeline
from app.models.knowledge import VectorStoreType, KnowledgeChunk


@dataclass
class HybridSearchResult:
    """Hybrid search result with combined scores"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    bm25_score: float
    dense_score: float
    metadata: Dict[str, Any]
    document_title: Optional[str] = None
    document_uuid: Optional[str] = None


class BM25Retriever:
    """
    BM25 keyword search implementation
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.doc_lengths: Dict[int, int] = defaultdict(int)
        self.avg_doc_length: float = 0.0
        self.total_docs = 0
        self.indexed = False
    
    def index_documents(self, chunks: List[KnowledgeChunk]) -> None:
        """
        Build BM25 index from chunks
        
        Args:
            chunks: List of KnowledgeChunk instances
        """
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = defaultdict(int)
        
        for chunk in chunks:
            # Tokenize
            tokens = self._tokenize(str(chunk.content))
            self.doc_lengths[int(chunk.id)] = len(tokens)
            
            # Count document frequencies
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = float(sum(self.doc_lengths.values()) / len(self.doc_lengths))
        
        self.total_docs = len(chunks)
        self.indexed = True
        
        logger.info(f"BM25 index built: {self.total_docs} documents, {len(self.doc_freqs)} unique terms")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        tokens = text.split()
        return tokens
    
    def search(
        self,
        query: str,
        chunks: List[KnowledgeChunk],
        top_k: int = 10
    ) -> List[tuple[int, float]]:
        """
        Search using BM25
        
        Args:
            query: Search query
            chunks: List of chunks to search
            top_k: Number of results
            
        Returns:
            List of (chunk_id, score) tuples
        """
        if not self.indexed:
            logger.warning("BM25 not indexed, returning empty results")
            return []
        
        query_tokens = self._tokenize(query)
        scores: List[Tuple[int, float]] = []
        
        for chunk in chunks:
            chunk_tokens = self._tokenize(str(chunk.content))
            score = self._calculate_bm25(query_tokens, chunk_tokens, int(chunk.id))
            scores.append((int(chunk.id), score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def _calculate_bm25(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_id: int
    ) -> float:
        """Calculate BM25 score"""
        score = 0.0
        doc_length = self.doc_lengths.get(doc_id, 0)
        
        for token in query_tokens:
            if token in doc_tokens:
                # Term frequency in document
                tf = doc_tokens.count(token)
                
                # Document frequency
                df = self.doc_freqs.get(token, 0)
                
                # IDF
                idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                score += idf * (numerator / denominator)
        
        return score


class DenseRetriever:
    """
    Dense vector retrieval using embeddings
    """
    
    def __init__(self, vector_store: Optional[BaseVectorStore] = None):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_pipeline = embedding_pipeline
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search using dense vector similarity
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult instances
        """
        # Generate query embedding
        from app.knowledge.embeddings import BaseEmbeddingProvider
        provider = self.embedding_pipeline.get_provider()
        query_embedding = await provider.embed(query)
        
        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
        
        logger.info(f"Dense retrieval returned {len(results)} results")
        return results


class HybridSearchEngine:
    """
    Hybrid search combining BM25 and dense retrieval
    """
    
    def __init__(
        self,
        bm25_weight: float = 0.3,
        dense_weight: float = 0.7,
        normalization_method: str = "minmax"
    ):
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.normalization_method = normalization_method
        self.bm25_retriever = BM25Retriever()
        self.dense_retriever = DenseRetriever()
    
    def index_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Index chunks for BM25"""
        self.bm25_retriever.index_documents(chunks)
    
    async def search(
        self,
        query: str,
        chunks: List[KnowledgeChunk],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True
    ) -> List[HybridSearchResult]:
        """
        Perform hybrid search
        
        Args:
            query: Search query
            chunks: List of chunks to search
            top_k: Number of results
            filters: Optional metadata filters
            use_hybrid: Whether to use hybrid or dense-only search
            
        Returns:
            List of HybridSearchResult instances
        """
        if not use_hybrid:
            # Dense-only search
            dense_results = await self.dense_retriever.search(query, top_k, filters)
            return [
                HybridSearchResult(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    content=r.content,
                    score=r.score,
                    bm25_score=0.0,
                    dense_score=r.score,
                    metadata=r.metadata,
                    document_title=r.document_title,
                    document_uuid=r.document_uuid
                )
                for r in dense_results
            ]
        
        # BM25 search
        bm25_results = self.bm25_retriever.search(query, chunks, top_k * 2)
        bm25_scores = {chunk_id: score for chunk_id, score in bm25_results}
        
        # Dense search
        dense_results = await self.dense_retriever.search(query, top_k * 2, filters)
        dense_scores = {r.chunk_id: r.score for r in dense_results}
        
        # Normalize scores
        normalized_bm25 = self._normalize_scores(bm25_scores, self.normalization_method)
        normalized_dense = self._normalize_scores(dense_scores, self.normalization_method)
        
        # Combine scores
        combined_scores = {}
        all_chunk_ids = set(normalized_bm25.keys()) | set(normalized_dense.keys())
        
        for chunk_id in all_chunk_ids:
            bm25_score = normalized_bm25.get(chunk_id, 0.0)
            dense_score = normalized_dense.get(chunk_id, 0.0)
            
            combined_score = (
                self.bm25_weight * bm25_score +
                self.dense_weight * dense_score
            )
            
            combined_scores[chunk_id] = {
                'combined': combined_score,
                'bm25': bm25_score,
                'dense': dense_score
            }
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['combined'],
            reverse=True
        )[:top_k]
        
        # Build result objects
        results = []
        for chunk_id, scores in sorted_results:
            # Find chunk details
            chunk = next((c for c in chunks if c.id == chunk_id), None)
            if not chunk:
                continue
            
            # Get document info
            from app.core.database import get_db
            from sqlalchemy import select
            from app.models.knowledge import KnowledgeDocument
            
            async for db in get_db():
                doc_result = await db.execute(
                    select(KnowledgeDocument).where(KnowledgeDocument.id == chunk.document_id)
                )
                doc = doc_result.scalar_one_or_none()
                
                results.append(HybridSearchResult(
                    chunk_id=int(chunk_id),
                    document_id=int(chunk.document_id),
                    content=str(chunk.content),
                    score=scores['combined'],
                    bm25_score=scores['bm25'],
                    dense_score=scores['dense'],
                    metadata=dict(chunk.metadata_json) if chunk.metadata_json else {},
                    document_title=str(doc.title) if doc else None,
                    document_uuid=str(doc.uuid) if doc else None
                ))
                break
        
        logger.info(f"Hybrid search returned {len(results)} results")
        return results
    
    def _normalize_scores(
        self,
        scores: Dict[int, float],
        method: str = "minmax"
    ) -> Dict[int, float]:
        """
        Normalize scores to [0, 1] range
        
        Args:
            scores: Dictionary of chunk_id -> score
            method: Normalization method (minmax, zscore, rank)
            
        Returns:
            Normalized scores
        """
        if not scores:
            return scores
        
        values = list(scores.values())
        
        if method == "minmax":
            min_val = min(values)
            max_val = max(values)
            if max_val == min_val:
                return {k: 0.5 for k in scores.keys()}
            return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}
        
        elif method == "zscore":
            import statistics
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 1.0
            if std_val == 0:
                return {k: 0.5 for k in scores.keys()}
            # Convert z-score to [0, 1]
            normalized = {}
            for k, v in scores.items():
                z = (v - mean_val) / std_val
                # Sigmoid to convert to [0, 1]
                normalized[k] = 1 / (1 + math.exp(-z))
            return normalized
        
        elif method == "rank":
            # Normalize by rank
            sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            rank_scores = {}
            for rank, (chunk_id, _) in enumerate(sorted_items):
                rank_scores[chunk_id] = 1.0 - (rank / len(sorted_items))
            return rank_scores
        
        else:
            return scores


class SearchFilter:
    """
    Search filter builder for metadata, tags, and date filtering
    """
    
    @staticmethod
    def build_filters(
        user_id: Optional[int] = None,
        language: Optional[str] = None,
        document_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build filter dictionary
        
        Args:
            user_id: User ID filter
            language: Language filter
            document_type: Document type filter
            date_from: Start date filter
            date_to: End date filter
            tags: Tag filters
            metadata_filters: Custom metadata filters
            
        Returns:
            Filter dictionary
        """
        filters: Dict[str, Any] = {}
        
        if user_id is not None:
            filters['user_id'] = user_id
        
        if language is not None:
            filters['language'] = language
        
        if document_type is not None:
            filters['document_type'] = document_type
        
        if date_from is not None or date_to is not None:
            filters['date_range'] = {
                'from': date_from,
                'to': date_to
            }
        
        if tags is not None:
            filters['tags'] = tags
        
        if metadata_filters is not None:
            filters.update(metadata_filters)
        
        return filters
    
    @staticmethod
    def apply_filters_to_chunks(
        chunks: List[KnowledgeChunk],
        filters: Dict[str, Any]
    ) -> List[KnowledgeChunk]:
        """
        Apply filters to chunks
        
        Args:
            chunks: List of chunks
            filters: Filter dictionary
            
        Returns:
            Filtered list of chunks
        """
        filtered = chunks
        
        if 'language' in filters:
            filtered = [
                c for c in filtered
                if c.metadata_json and c.metadata_json.get('language') == filters['language']
            ]
        
        if 'document_type' in filters:
            filtered = [
                c for c in filtered
                if c.metadata_json and c.metadata_json.get('document_type') == filters['document_type']
            ]
        
        if 'tags' in filters:
            tags = filters['tags']
            filtered = [
                c for c in filtered
                if c.metadata_json and any(tag in c.metadata_json.get('tags', []) for tag in tags)
            ]
        
        return filtered


class SearchResultMerger:
    """
    Merge and deduplicate search results
    """
    
    @staticmethod
    def merge_results(
        results: List[HybridSearchResult],
        deduplicate: bool = True,
        similarity_threshold: float = 0.95
    ) -> List[HybridSearchResult]:
        """
        Merge and deduplicate results
        
        Args:
            results: List of search results
            deduplicate: Whether to deduplicate
            similarity_threshold: Threshold for near-duplicate detection
            
        Returns:
            Merged results
        """
        if not deduplicate:
            return results
        
        # Deduplicate by content similarity
        unique_results = []
        seen_contents = set()
        
        for result in results:
            # Simple hash-based deduplication
            content_hash = hash(result.content)
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    @staticmethod
    def diversify_results(
        results: List[HybridSearchResult],
        diversity_factor: float = 0.5
    ) -> List[HybridSearchResult]:
        """
        Diversify results using Maximal Marginal Relevance (MMR)
        
        Args:
            results: List of search results
            diversity_factor: Diversity factor (0 = no diversity, 1 = maximum diversity)
            
        Returns:
            Diversified results
        """
        if not results or diversity_factor == 0:
            return results
        
        # Simple document-based diversification
        diversified = []
        seen_documents = set()
        
        for result in results:
            if result.document_id not in seen_documents:
                diversified.append(result)
                seen_documents.add(result.document_id)
            elif len(diversified) < len(results) * (1 - diversity_factor):
                diversified.append(result)
        
        return diversified


# Singleton instance (lazy-loaded)
_hybrid_search_engine: Optional[HybridSearchEngine] = None

def get_hybrid_search_engine() -> HybridSearchEngine:
    """Get or create the hybrid search engine singleton"""
    global _hybrid_search_engine
    if _hybrid_search_engine is None:
        _hybrid_search_engine = HybridSearchEngine()
    return _hybrid_search_engine

# Backwards compatibility - use get_hybrid_search_engine() instead
hybrid_search_engine = None  # Will be initialized on first access
