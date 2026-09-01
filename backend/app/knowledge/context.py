"""
Context Builder
Token budgeting, automatic context compression, source attribution, citation generation, confidence scoring
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from loguru import logger

from app.knowledge.reranking import RerankedResult


@dataclass
class Citation:
    """Citation for a source"""
    chunk_id: int
    document_id: int
    document_title: str
    document_uuid: str
    page_number: Optional[int] = None
    confidence: float = 0.0
    relevance_score: float = 0.0


@dataclass
class BuiltContext:
    """Built context with citations"""
    context_text: str
    citations: List[Citation]
    total_tokens: int
    total_sources: int
    average_confidence: float
    metadata: Dict[str, Any]


class TokenBudgetManager:
    """
    Manage token budget for context building
    """
    
    def __init__(self, max_tokens: int = 4000, reserve_tokens: int = 500):
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.available_tokens = max_tokens - reserve_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def allocate_budget(
        self,
        results: List[RerankedResult],
        query_tokens: int = 0
    ) -> Dict[int, int]:
        """
        Allocate token budget to results
        
        Args:
            results: Reranked results
            query_tokens: Tokens used by query
            
        Returns:
            Dictionary of chunk_id -> allocated tokens
        """
        available = self.available_tokens - query_tokens
        if available <= 0:
            return {}
        
        # Calculate total estimated tokens
        total_estimated = sum(self.estimate_tokens(r.content) for r in results)
        
        if total_estimated <= available:
            # All results fit
            return {r.chunk_id: self.estimate_tokens(r.content) for r in results}
        
        # Proportional allocation based on score
        allocation = {}
        remaining = available
        
        for result in results:
            if remaining <= 0:
                break
            
            # Proportional to score
            weight = result.score / sum(r.score for r in results)
            allocated = int(weight * available)
            
            # Cap at actual content size
            actual_size = self.estimate_tokens(result.content)
            allocated = min(allocated, actual_size)
            
            allocation[result.chunk_id] = allocated
            remaining -= allocated
        
        return allocation


class ContextCompressor:
    """
    Compress context to fit within token budget
    """
    
    def compress(
        self,
        text: str,
        target_tokens: int,
        method: str = "truncate"
    ) -> str:
        """
        Compress text to target token count
        
        Args:
            text: Input text
            target_tokens: Target token count
            method: Compression method (truncate, summarize, extractive)
            
        Returns:
            Compressed text
        """
        current_tokens = self._estimate_tokens(text)
        
        if current_tokens <= target_tokens:
            return text
        
        if method == "truncate":
            return self._truncate(text, target_tokens)
        elif method == "summarize":
            return self._summarize(text, target_tokens)
        elif method == "extractive":
            return self._extractive(text, target_tokens)
        else:
            return self._truncate(text, target_tokens)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4
    
    def _truncate(self, text: str, target_tokens: int) -> str:
        """Truncate text to target tokens"""
        target_chars = target_tokens * 4
        if len(text) <= target_chars:
            return text
        
        # Truncate at word boundary
        truncated = text[:target_chars]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def _summarize(self, text: str, target_tokens: int) -> str:
        """Summarize text (placeholder for actual summarization)"""
        # In production, use an LLM or summarization model
        # For now, use extractive approach
        return self._extractive(text, target_tokens)
    
    def _extractive(self, text: str, target_tokens: int) -> str:
        """Extractive summarization - keep most important sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by position and length
        scored = []
        for i, sentence in enumerate(sentences):
            score = len(sentence) / max(len(s) for s in sentences) if sentences else 0
            # Prefer middle sentences
            position_score = 1 - abs(i - len(sentences) / 2) / (len(sentences) / 2)
            scored.append((sentence, score * position_score))
        
        # Sort by score and take top
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Build summary
        summary = []
        current_tokens = 0
        
        for sentence, score in scored:
            sentence_tokens = self._estimate_tokens(sentence)
            if current_tokens + sentence_tokens <= target_tokens:
                summary.append(sentence)
                current_tokens += sentence_tokens
        
        return ' '.join(summary)


class CitationGenerator:
    """
    Generate citations for sources
    """
    
    def generate_citations(
        self,
        results: List[RerankedResult]
    ) -> List[Citation]:
        """
        Generate citations from results
        
        Args:
            results: Reranked results
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        for result in results:
            citation = Citation(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_title=result.document_title or "Unknown Document",
                document_uuid=result.document_uuid or "",
                page_number=result.metadata.get('page_number'),
                confidence=result.score,
                relevance_score=result.score
            )
            citations.append(citation)
        
        return citations
    
    def format_citations(
        self,
        citations: List[Citation],
        style: str = "numeric"
    ) -> str:
        """
        Format citations for display
        
        Args:
            citations: List of Citation objects
            style: Citation style (numeric, apa, mla)
            
        Returns:
            Formatted citation string
        """
        if style == "numeric":
            return self._format_numeric(citations)
        elif style == "apa":
            return self._format_apa(citations)
        elif style == "mla":
            return self._format_mla(citations)
        else:
            return self._format_numeric(citations)
    
    def _format_numeric(self, citations: List[Citation]) -> str:
        """Numeric citation style [1], [2], etc."""
        return " ".join(f"[{i+1}]" for i in range(len(citations)))
    
    def _format_apa(self, citations: List[Citation]) -> str:
        """APA citation style"""
        formatted = []
        for citation in citations:
            formatted.append(f"{citation.document_title} (Source: {citation.document_uuid[:8]})")
        return "; ".join(formatted)
    
    def _format_mla(self, citations: List[Citation]) -> str:
        """MLA citation style"""
        formatted = []
        for citation in citations:
            formatted.append(f'"{citation.document_title}"')
        return ", ".join(formatted)


class ConfidenceScorer:
    """
    Calculate confidence scores for context
    """
    
    def calculate_confidence(
        self,
        results: List[RerankedResult],
        query: str
    ) -> Dict[str, float]:
        """
        Calculate confidence metrics
        
        Args:
            results: Reranked results
            query: Original query
            
        Returns:
            Dictionary of confidence metrics
        """
        if not results:
            return {
                'average_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'query_relevance': 0.0
            }
        
        scores = [r.score for r in results]
        
        # Calculate metrics
        avg_confidence = sum(scores) / len(scores)
        min_confidence = min(scores)
        max_confidence = max(scores)
        
        # Query relevance (based on top result)
        query_relevance = scores[0] if scores else 0.0
        
        return {
            'average_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'query_relevance': query_relevance
        }
    
    def calculate_source_reliability(
        self,
        results: List[RerankedResult]
    ) -> Dict[int, float]:
        """
        Calculate source reliability scores
        
        Args:
            results: Reranked results
            
        Returns:
            Dictionary of document_id -> reliability score
        """
        reliability = {}
        
        # Group by document
        doc_scores: Dict[int, List[float]] = {}
        for result in results:
            if result.document_id not in doc_scores:
                doc_scores[result.document_id] = []
            doc_scores[result.document_id].append(result.score)
        
        # Calculate reliability as average score
        for doc_id, scores in doc_scores.items():
            reliability[doc_id] = sum(scores) / len(scores)
        
        return reliability


class ContextBuilder:
    """
    Main context builder
    """
    
    def __init__(
        self,
        max_tokens: int = 4000,
        compression_method: str = "truncate",
        citation_style: str = "numeric"
    ):
        self.token_budget_manager = TokenBudgetManager(max_tokens)
        self.context_compressor = ContextCompressor()
        self.citation_generator = CitationGenerator()
        self.confidence_scorer = ConfidenceScorer()
        self.compression_method = compression_method
        self.citation_style = citation_style
    
    def build_context(
        self,
        query: str,
        results: List[RerankedResult],
        include_citations: bool = True
    ) -> BuiltContext:
        """
        Build context from search results
        
        Args:
            query: Original query
            results: Reranked search results
            include_citations: Whether to include citations
            
        Returns:
            BuiltContext object
        """
        if not results:
            return BuiltContext(
                context_text="",
                citations=[],
                total_tokens=0,
                total_sources=0,
                average_confidence=0.0,
                metadata={}
            )
        
        # Allocate token budget
        query_tokens = self.token_budget_manager.estimate_tokens(query)
        allocation = self.token_budget_manager.allocate_budget(results, query_tokens)
        
        # Build context with allocated budget
        context_parts = []
        citations = []
        total_tokens = query_tokens
        
        for result in results:
            if result.chunk_id not in allocation:
                continue
            
            allocated_tokens = allocation[result.chunk_id]
            
            # Compress content to fit allocation
            compressed = self.context_compressor.compress(
                result.content,
                allocated_tokens,
                self.compression_method
            )
            
            context_parts.append(compressed)
            total_tokens += self.token_budget_manager.estimate_tokens(compressed)
            
            # Generate citation
            if include_citations:
                citation = self.citation_generator.generate_citations([result])[0]
                citations.append(citation)
        
        # Combine context
        context_text = "\n\n".join(context_parts)
        
        # Calculate confidence
        confidence_metrics = self.confidence_scorer.calculate_confidence(results, query)
        
        # Build metadata
        metadata = {
            'query': query,
            'compression_method': self.compression_method,
            'token_allocation': allocation,
            'confidence_metrics': confidence_metrics,
        }
        
        built_context = BuiltContext(
            context_text=context_text,
            citations=citations,
            total_tokens=total_tokens,
            total_sources=len(set(r.document_id for r in results)),
            average_confidence=confidence_metrics['average_confidence'],
            metadata=metadata
        )
        
        logger.info(
            f"Context built: {total_tokens} tokens, {len(citations)} citations, "
            f"{built_context.total_sources} sources"
        )
        
        return built_context
    
    def build_context_with_prompt(
        self,
        query: str,
        results: List[RerankedResult],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Build complete prompt with context for LLM
        
        Args:
            query: Original query
            results: Reranked search results
            system_prompt: Optional system prompt
            
        Returns:
            Complete prompt string
        """
        # Build context
        built_context = self.build_context(query, results)
        
        # Format citations
        citation_text = ""
        if built_context.citations:
            citation_text = "\n\nSources:\n" + self.citation_generator.format_citations(
                built_context.citations,
                self.citation_style
            )
        
        # Build prompt
        if system_prompt:
            prompt = f"{system_prompt}\n\n"
        else:
            prompt = ""
        
        prompt += f"Context:\n{built_context.context_text}{citation_text}\n\n"
        prompt += f"Question: {query}\n\n"
        prompt += "Please answer the question based on the provided context. "
        prompt += "If the context doesn't contain enough information to answer the question, "
        prompt += "please state that clearly."
        
        return prompt


# Singleton instance (lazy-loaded)
_context_builder: Optional[ContextBuilder] = None

def get_context_builder() -> ContextBuilder:
    """Get or create the context builder singleton"""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder

# Backwards compatibility - use get_context_builder() instead
context_builder = None  # Will be initialized on first access
