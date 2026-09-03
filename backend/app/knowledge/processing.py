"""
Document Processing System
Metadata extraction, language detection, duplicate detection, checksum validation, version tracking
"""
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import Counter

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument, DocumentStatus
from app.knowledge.ingestion import DocumentExtractor


class MetadataExtractor:
    """
    Extract metadata from documents
    """
    
    def __init__(self) -> None:
        pass
    
    def extract_metadata(
        self,
        content: str,
        filename: str,
        doc_type: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from document content
        
        Args:
            content: Document text content
            filename: Original filename
            doc_type: Document type
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'filename': filename,
            'file_type': doc_type,
            'character_count': len(content),
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'has_tables': '<table' in content.lower(),
            'has_images': '<img' in content.lower() or doc_type in ['pdf', 'docx', 'pptx'],
            'has_code': '```' in content or '<code' in content.lower(),
            'avg_word_length': self._calculate_avg_word_length(content),
            'avg_sentence_length': self._calculate_avg_sentence_length(content),
        }
        
        # Extract potential title from first line or filename
        lines = content.strip().split('\n')
        if lines:
            metadata['potential_title'] = lines[0][:200]
        
        return metadata
    
    def _calculate_avg_word_length(self, content: str) -> float:
        """Calculate average word length"""
        words = content.split()
        if not words:
            return 0.0
        return sum(len(word) for word in words) / len(words)
    
    def _calculate_avg_sentence_length(self, content: str) -> float:
        """Calculate average sentence length in words"""
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if not sentences:
            return 0.0
        word_counts = [len(s.split()) for s in sentences]
        return sum(word_counts) / len(word_counts)


class LanguageDetector:
    """
    Detect document language using FastText
    """

    def __init__(self) -> None:
        self.model = None
        # Lazy load model - don't load during import
        self._model_loaded = False

    def _load_model(self) -> None:
        """Load FastText language detection model"""
        if self._model_loaded:
            return

        try:
            import fasttext
            # Use lightweight language detection model
            model_path = 'lid.176.bin'  # FastText language identification model
            self.model = fasttext.load_model(model_path)
            logger.info("FastText language detection model loaded")
        except Exception as e:
            logger.warning(f"Failed to load FastText model: {e}. Using fallback detection.")
            self.model = None

        self._model_loaded = True
    
    def detect_language(self, content: str) -> tuple[str, float]:
        """
        Detect language of content
        
        Args:
            content: Document text content
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        if self.model:
            try:
                # FastText expects lowercase text
                prediction = self.model.predict(content.lower(), k=1)
                lang_code = prediction[0][0].replace('__label__', '')
                confidence = float(prediction[1][0])
                return lang_code, confidence
            except Exception as e:
                logger.warning(f"FastText detection failed: {e}. Using fallback.")
        
        # Fallback: simple heuristic
        self._model_loaded = True  # Mark as attempted even if using fallback
        return self._fallback_language_detection(content)
    
    def _fallback_language_detection(self, content: str) -> tuple[str, float]:
        """
        Fallback language detection using heuristics
        
        Args:
            content: Document text content
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        # Simple character-based detection
        content_lower = content.lower()
        
        # Check for common English words
        english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'it', 'on']
        english_count = sum(1 for word in english_words if word in content_lower.split())
        
        # Check for common Spanish words
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se']
        spanish_count = sum(1 for word in spanish_words if word in content_lower.split())
        
        # Check for common French words
        french_words = ['le', 'de', 'et', 'à', 'un', 'il', 'avoir', 'ne', 'je', 'son']
        french_count = sum(1 for word in french_words if word in content_lower.split())
        
        # Determine most likely language
        counts = {
            'en': english_count,
            'es': spanish_count,
            'fr': french_count,
        }
        
        max_lang = max(counts.keys(), key=lambda k: counts[k])
        max_count = counts[max_lang]
        total_words = len(content_lower.split())
        
        confidence = max_count / total_words if total_words > 0 else 0.0
        
        return max_lang, confidence


class DuplicateDetector:
    """
    Detect duplicate and near-duplicate documents
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
    
    def is_duplicate(
        self,
        content: str,
        existing_content: str
    ) -> bool:
        """
        Check if content is a duplicate of existing content
        
        Args:
            content: New document content
            existing_content: Existing document content
            
        Returns:
            True if duplicate, False otherwise
        """
        # Exact match
        if content == existing_content:
            return True
        
        # Similarity check
        similarity = self._calculate_similarity(content, existing_content)
        return similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two texts using Jaccard similarity
        
        Args:
            content1: First text
            content2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Tokenize
        tokens1 = set(content1.lower().split())
        tokens2 = set(content2.lower().split())
        
        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def find_near_duplicates(
        self,
        content: str,
        existing_documents: List[str]
    ) -> List[tuple[int, float]]:
        """
        Find near-duplicate documents
        
        Args:
            content: New document content
            existing_documents: List of existing document contents
            
        Returns:
            List of (index, similarity_score) tuples for near-duplicates
        """
        near_duplicates = []
        
        for idx, existing_content in enumerate(existing_documents):
            similarity = self._calculate_similarity(content, existing_content)
            if similarity >= self.similarity_threshold:
                near_duplicates.append((idx, similarity))
        
        # Sort by similarity descending
        near_duplicates.sort(key=lambda x: x[1], reverse=True)
        
        return near_duplicates


class VersionTracker:
    """
    Track document versions and changes
    """
    
    def __init__(self) -> None:
        pass
    
    def calculate_version_difference(
        self,
        old_content: str,
        new_content: str
    ) -> Dict[str, Any]:
        """
        Calculate differences between document versions
        
        Args:
            old_content: Previous version content
            new_content: New version content
            
        Returns:
            Dictionary with difference metrics
        """
        old_words = set(old_content.lower().split())
        new_words = set(new_content.lower().split())
        
        added_words = new_words - old_words
        removed_words = old_words - new_words
        
        return {
            'added_words': len(added_words),
            'removed_words': len(removed_words),
            'changed_ratio': len(added_words | removed_words) / len(old_words | new_words) if old_words | new_words else 0,
            'added_word_sample': list(added_words)[:10],
            'removed_word_sample': list(removed_words)[:10],
        }
    
    def should_create_new_version(
        self,
        old_content: str,
        new_content: str,
        change_threshold: float = 0.1
    ) -> bool:
        """
        Determine if changes warrant a new version
        
        Args:
            old_content: Previous version content
            new_content: New version content
            change_threshold: Minimum change ratio to create new version
            
        Returns:
            True if new version should be created
        """
        if old_content == new_content:
            return False
        
        diff = self.calculate_version_difference(old_content, new_content)
        return bool(diff['changed_ratio'] >= change_threshold)


class DocumentProcessor:
    """
    Main document processing orchestrator
    """
    
    def __init__(self) -> None:
        self.metadata_extractor = MetadataExtractor()
        self.language_detector = LanguageDetector()
        self.duplicate_detector = DuplicateDetector()
        self.version_tracker = VersionTracker()
        self.document_extractor = DocumentExtractor()
    
    async def process_document(
        self,
        document: KnowledgeDocument,
        content: bytes,
        existing_documents: Optional[List[tuple[str, str]]] = None,
        db: Optional[AsyncSession] = None
    ) -> KnowledgeDocument:
        """
        Process document: extract text, metadata, detect language, check duplicates
        
        Args:
            document: KnowledgeDocument instance
            content: File content
            existing_documents: List of (document_id, content) tuples for duplicate checking
            db: Optional database session (if not provided, creates new one)
            
        Returns:
            Updated KnowledgeDocument instance
        """
        from app.models.knowledge import DocumentType
        from app.core.database import get_db
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        
        if db is None:
            async for session in get_db():
                return await self._process_in_session(
                    session, document, content, existing_documents
                )
        else:
            return await self._process_in_session(
                db, document, content, existing_documents
            )
    
    async def _process_in_session(
        self,
        db: AsyncSession,
        document: KnowledgeDocument,
        content: bytes,
        existing_documents: Optional[List[tuple[str, str]]]
    ) -> KnowledgeDocument:
        """Internal method to process document in a specific session"""
        from app.models.knowledge import DocumentType
        
        # Extract text content
        doc_type = DocumentType(document.document_type.value)
        text_content = await self.document_extractor.extract_text(
            content, doc_type, str(document.file_name)
        )
        
        # Update document with processed content
        document.processed_content = text_content  # type: ignore[assignment]
        document.character_count = len(text_content)  # type: ignore[assignment]
        document.token_count = len(text_content.split())  # type: ignore[assignment]
        
        # Extract metadata
        metadata = self.metadata_extractor.extract_metadata(
            text_content, str(document.file_name), str(document.document_type.value)
        )
        document.metadata_json = metadata  # type: ignore[assignment]
        
        # Detect language
        language, confidence = self.language_detector.detect_language(text_content)
        document.language = language  # type: ignore[assignment]
        
        # Add language confidence to metadata
        metadata['language_confidence'] = confidence
        document.metadata_json = metadata  # type: ignore[assignment]
        
        # Check for duplicates
        if existing_documents:
            for doc_id, existing_content in existing_documents:
                if self.duplicate_detector.is_duplicate(text_content, existing_content):
                    logger.warning(f"Duplicate detected for document {document.uuid}")
                    document.status = DocumentStatus.FAILED
                    document.metadata_json = {  # type: ignore[assignment]
                        **metadata,
                        'duplicate_of': doc_id,
                        'duplicate_reason': 'content_similarity'
                    }
                    await db.commit()
                    await db.refresh(document)
                    return document
        
        # Update status
        document.status = DocumentStatus.PROCESSING
        await db.commit()
        await db.refresh(document)
        
        logger.info(
            f"Document processed: {document.uuid}, "
            f"language={language}, tokens={document.token_count}"
        )
        
        return document


# Lazy-loaded document processor instance
_document_processor = None


def get_document_processor():
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


# Backward compatibility
document_processor = property(lambda: get_document_processor())
