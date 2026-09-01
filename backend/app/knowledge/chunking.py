"""
Chunking Pipeline
Semantic, recursive, sliding window, parent/child, adaptive chunking strategies
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    ChunkingStrategy,
)


@dataclass
class Chunk:
    """Data class for a text chunk"""
    content: str
    index: int
    metadata: Dict[str, Any]
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    page_number: Optional[int] = None
    parent_id: Optional[int] = None
    is_parent: bool = False


class BaseChunker(ABC):
    """Base class for chunking strategies"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Chunk text according to strategy
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects
        """
        pass


class SemanticChunker(BaseChunker):
    """
    Semantic chunking using sentence boundaries and topic segmentation
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Chunk text semantically by sentence boundaries
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        char_position = 0
        
        for sentence in sentences:
            # Check if adding sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and len(current_chunk) >= self.min_chunk_size:
                # Save current chunk
                chunks.append(Chunk(
                    content=current_chunk.strip(),
                    index=chunk_index,
                    metadata={
                        'document_id': document_id,
                        'chunking_strategy': ChunkingStrategy.SEMANTIC.value,
                        'sentence_count': len(self._split_sentences(current_chunk)),
                    },
                    start_char=char_position - len(current_chunk),
                    end_char=char_position
                ))
                chunk_index += 1
                char_position = len(current_chunk)
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap(current_chunk)
                char_position = len(current_chunk)
            
            current_chunk += " " + sentence if current_chunk else sentence
        
        # Add remaining content
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(Chunk(
                content=current_chunk.strip(),
                index=chunk_index,
                metadata={
                    'document_id': document_id,
                    'chunking_strategy': ChunkingStrategy.SEMANTIC.value,
                    'sentence_count': len(self._split_sentences(current_chunk)),
                },
                start_char=char_position - len(current_chunk),
                end_char=len(text)
            ))
        
        logger.info(f"Semantic chunking: {len(chunks)} chunks created")
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting using regex
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap(self, text: str) -> str:
        """Get overlapping text from end of chunk"""
        words = text.split()
        overlap_words = words[-self.chunk_overlap // 5:] if len(words) > self.chunk_overlap // 5 else words
        return " ".join(overlap_words)


class RecursiveChunker(BaseChunker):
    """
    Recursive chunking using document structure (headers, paragraphs)
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        headers: Optional[List[str]] = None
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.headers = headers or ['#', '##', '###', '####', '#####']
    
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Chunk text recursively by headers
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0
        
        # Split by headers
        sections = self._split_by_headers(text)
        
        for section_title, section_content in sections:
            if len(section_content) <= self.chunk_size:
                chunks.append(Chunk(
                    content=section_content.strip(),
                    index=chunk_index,
                    metadata={
                        'document_id': document_id,
                        'chunking_strategy': ChunkingStrategy.RECURSIVE.value,
                        'section_title': section_title,
                    }
                ))
                chunk_index += 1
            else:
                # Recursively chunk large sections
                sub_chunks = self._recursive_split(section_content, chunk_index)
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
        
        logger.info(f"Recursive chunking: {len(chunks)} chunks created")
        return chunks
    
    def _split_by_headers(self, text: str) -> List[tuple[str, str]]:
        """Split text by markdown headers"""
        sections = []
        lines = text.split('\n')
        current_section: List[str] = []
        current_title = "Introduction"
        
        for line in lines:
            if any(line.startswith(h) for h in self.headers):
                # Save previous section
                if current_section:
                    sections.append((current_title, '\n'.join(current_section)))
                    current_section = []
                current_title = line.strip()
            else:
                current_section.append(line)
        
        # Add last section
        if current_section:
            sections.append((current_title, '\n'.join(current_section)))
        
        return sections
    
    def _recursive_split(self, text: str, start_index: int) -> List[Chunk]:
        """Recursively split text into chunks"""
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = start_index
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(Chunk(
                        content=current_chunk.strip(),
                        index=chunk_index,
                        metadata={
                            'chunking_strategy': ChunkingStrategy.RECURSIVE.value,
                        }
                    ))
                    chunk_index += 1
                    current_chunk = ""
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(Chunk(
                content=current_chunk.strip(),
                index=chunk_index,
                metadata={
                    'chunking_strategy': ChunkingStrategy.RECURSIVE.value,
                }
            ))
        
        return chunks


class SlidingWindowChunker(BaseChunker):
    """
    Sliding window chunking with configurable overlap
    """
    
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Chunk text using sliding window
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Adjust end to word boundary
            if end < len(text):
                end = text.rfind(' ', start, end)
                if end == -1:
                    end = start + self.chunk_size
            
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunks.append(Chunk(
                    content=chunk_content,
                    index=chunk_index,
                    metadata={
                        'document_id': document_id,
                        'chunking_strategy': ChunkingStrategy.SLIDING_WINDOW.value,
                    },
                    start_char=start,
                    end_char=end
                ))
                chunk_index += 1
            
            # Move window with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        
        logger.info(f"Sliding window chunking: {len(chunks)} chunks created")
        return chunks


class ParentChildChunker(BaseChunker):
    """
    Parent/child chunking for context preservation
    """
    
    def __init__(
        self,
        parent_chunk_size: int = 2000,
        child_chunk_size: int = 500,
        child_overlap: int = 100
    ):
        super().__init__(child_chunk_size, child_overlap)
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap
    
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Create parent and child chunks
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects (both parent and child)
        """
        chunks = []
        parent_index = 0
        child_index = 0
        
        # Create parent chunks
        parent_chunks = self._create_parent_chunks(text)
        
        for parent_chunk in parent_chunks:
            # Add parent chunk
            parent_chunk_obj = Chunk(
                content=parent_chunk['content'],
                index=parent_index,
                metadata={
                    'document_id': document_id,
                    'chunking_strategy': ChunkingStrategy.PARENT_CHILD.value,
                    'is_parent': True,
                },
                start_char=parent_chunk['start'],
                end_char=parent_chunk['end'],
                is_parent=True
            )
            chunks.append(parent_chunk_obj)
            
            # Create child chunks from parent
            child_chunks = self._create_child_chunks(
                parent_chunk['content'],
                parent_index
            )
            
            for child_chunk in child_chunks:
                chunks.append(Chunk(
                    content=child_chunk['content'],
                    index=child_index,
                    metadata={
                        'document_id': document_id,
                        'chunking_strategy': ChunkingStrategy.PARENT_CHILD.value,
                        'is_parent': False,
                        'parent_index': parent_index,
                    },
                    parent_id=parent_index,
                    is_parent=False
                ))
                child_index += 1
            
            parent_index += 1
        
        logger.info(f"Parent/Child chunking: {len(chunks)} chunks created ({parent_index} parents, {child_index} children)")
        return chunks
    
    def _create_parent_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create large parent chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.parent_chunk_size
            if end < len(text):
                end = text.rfind('\n\n', start, end)
                if end == -1:
                    end = start + self.parent_chunk_size
            
            chunks.append({
                'content': text[start:end].strip(),
                'start': start,
                'end': end
            })
            
            start = end
            if start >= len(text):
                break
        
        return chunks
    
    def _create_child_chunks(self, parent_text: str, parent_index: int) -> List[Dict[str, Any]]:
        """Create small child chunks from parent"""
        chunks = []
        start = 0
        
        while start < len(parent_text):
            end = start + self.child_chunk_size
            if end < len(parent_text):
                end = parent_text.rfind(' ', start, end)
                if end == -1:
                    end = start + self.child_chunk_size
            
            chunks.append({
                'content': parent_text[start:end].strip(),
            })
            
            start = end - self.child_overlap
            if start < 0:
                start = 0
        
        return chunks


class AdaptiveChunker(BaseChunker):
    """
    Adaptive chunking based on content density and structure
    """
    
    def __init__(
        self,
        base_chunk_size: int = 1000,
        min_chunk_size: int = 200,
        max_chunk_size: int = 2000
    ):
        super().__init__(base_chunk_size, 0)
        self.base_chunk_size = base_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str, document_id: int) -> List[Chunk]:
        """
        Chunk text adaptively based on content characteristics
        
        Args:
            text: Input text
            document_id: Document ID
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            # Calculate optimal chunk size based on content
            chunk_size = self._calculate_adaptive_size(text, start)
            
            end = start + chunk_size
            if end < len(text):
                end = text.rfind('\n\n', start, end)
                if end == -1:
                    end = start + chunk_size
            
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                density = self._calculate_density(chunk_content)
                chunks.append(Chunk(
                    content=chunk_content,
                    index=chunk_index,
                    metadata={
                        'document_id': document_id,
                        'chunking_strategy': ChunkingStrategy.ADAPTIVE.value,
                        'adaptive_size': chunk_size,
                        'content_density': density,
                    },
                    start_char=start,
                    end_char=end
                ))
                chunk_index += 1
            
            start = end
        
        logger.info(f"Adaptive chunking: {len(chunks)} chunks created")
        return chunks
    
    def _calculate_adaptive_size(self, text: str, position: int) -> int:
        """Calculate adaptive chunk size based on content"""
        remaining = len(text) - position
        
        # Check for structural boundaries
        next_header = text.find('\n#', position, position + self.max_chunk_size)
        next_section = text.find('\n\n', position, position + self.max_chunk_size)
        
        if next_header != -1 and next_header < self.base_chunk_size:
            return min(next_header - position, self.max_chunk_size)
        
        if next_section != -1 and next_section < self.base_chunk_size:
            return min(next_section - position, self.max_chunk_size)
        
        # Use base size for regular content
        return min(self.base_chunk_size, remaining)
    
    def _calculate_density(self, text: str) -> float:
        """Calculate content density (information per character)"""
        if not text:
            return 0.0
        
        words = text.split()
        unique_words = len(set(word.lower() for word in words))
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        return unique_words / total_words


class ChunkingPipeline:
    """
    Main chunking pipeline that selects and executes chunking strategy
    """
    
    def __init__(self) -> None:
        self.chunkers: Dict[ChunkingStrategy, Any] = {
            ChunkingStrategy.SEMANTIC: SemanticChunker,
            ChunkingStrategy.RECURSIVE: RecursiveChunker,
            ChunkingStrategy.SLIDING_WINDOW: SlidingWindowChunker,
            ChunkingStrategy.PARENT_CHILD: ParentChildChunker,
            ChunkingStrategy.ADAPTIVE: AdaptiveChunker,
        }
    
    async def chunk_document(
        self,
        document: KnowledgeDocument,
        text: str,
        db: Optional[AsyncSession] = None
    ) -> List[KnowledgeChunk]:
        """
        Chunk document using configured strategy
        
        Args:
            document: KnowledgeDocument instance
            text: Processed text content
            db: Optional database session (if not provided, creates new one)
            
        Returns:
            List of KnowledgeChunk instances
        """
        from app.core.database import get_db
        
        # Get chunker based on document strategy
        chunker_class = self.chunkers.get(str(document.chunking_strategy), SemanticChunker)  # type: ignore
        chunker = chunker_class(
            chunk_size=int(document.chunk_size),
            chunk_overlap=int(document.chunk_overlap)
        )
        
        # Chunk text
        chunks = chunker.chunk(text, document.id)
        
        # Save chunks to database
        if db is None:
            async for session in get_db():
                return await self._save_chunks_in_session(session, chunks, document)
        else:
            return await self._save_chunks_in_session(db, chunks, document)
    
    async def _save_chunks_in_session(
        self,
        db: AsyncSession,
        chunks: List[Chunk],
        document: KnowledgeDocument
    ) -> List[KnowledgeChunk]:
        """Internal method to save chunks in a specific session"""
        knowledge_chunks = []
        
        for chunk in chunks:
            knowledge_chunk = KnowledgeChunk(
                document_id=document.id,
                content=chunk.content,
                chunk_index=chunk.index,
                metadata_json=chunk.metadata,
                page_number=chunk.page_number,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                is_parent=chunk.is_parent,
                token_count=len(chunk.content.split()),
                character_count=len(chunk.content)
            )
            db.add(knowledge_chunk)
            knowledge_chunks.append(knowledge_chunk)
        
        await db.commit()
        
        # Refresh to get IDs
        for kc in knowledge_chunks:
            await db.refresh(kc)
        
        # Update parent-child relationships
        for kc in knowledge_chunks:
            if kc.metadata_json and 'parent_index' in kc.metadata_json:
                parent_idx = kc.metadata_json['parent_index']
                parent_chunk = next(
                    (c for c in knowledge_chunks if c.chunk_index == parent_idx and c.is_parent),
                    None
                )
                if parent_chunk:
                    kc.parent_chunk_id = parent_chunk.id  # type: ignore[assignment]
        
        await db.commit()
        
        logger.info(f"Created {len(knowledge_chunks)} chunks for document {document.uuid}")
        
        return knowledge_chunks


# Singleton instance
chunking_pipeline = ChunkingPipeline()
