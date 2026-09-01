"""
Document Processing Tasks
Celery tasks for asynchronous document processing, indexing, and cleanup
"""
from celery import Task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.worker import celery_app
from app.core.database import AsyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.models.knowledge import KnowledgeDocument, DocumentStatus as KnowledgeDocumentStatus
from app.models.file import File as FileModel


class DatabaseTask(Task):
    """Base task with database session management"""
    _db: Optional[AsyncSession] = None

    @property
    def db(self) -> AsyncSession:
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            import asyncio
            asyncio.run(self._db.close())
        super().after_return(*args, **kwargs)


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.document_tasks.process_document')
def process_document(self, document_id: int) -> dict:
    """
    Process a document asynchronously
    
    Args:
        document_id: Document ID to process
        
    Returns:
        Processing result
    """
    import asyncio
    
    async def _process():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Document {document_id} not found")
                return {"status": "error", "message": "Document not found"}
            
            # Process document using knowledge pipeline
            from app.knowledge.processing import document_processor
            from app.knowledge.ingestion import document_extractor
            
            # Get file content
            file_result = await db.execute(
                select(FileModel).where(FileModel.id == document.file_id)
            )
            file_record = file_result.scalar_one_or_none()
            
            if file_record:
                content = await document_extractor.extract_content(file_record.storage_path)
                document = await document_processor.process_document(document, content, db=db)
            
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.now(timezone.utc)
            await db.commit()
            
            logger.info(f"Document {document_id} processed successfully")
            return {"status": "success", "document_id": document_id}
    
    return asyncio.run(_process())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.document_tasks.index_document')
def index_document(self, document_id: int) -> dict:
    """
    Index a document asynchronously
    
    Args:
        document_id: Document ID to index
        
    Returns:
        Indexing result
    """
    import asyncio
    
    async def _index():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Knowledge document {document_id} not found")
                return {"status": "error", "message": "Document not found"}
            
            # Index document using knowledge pipeline
            from app.knowledge.chunking import chunking_pipeline
            from app.knowledge.embeddings import embedding_pipeline
            from app.knowledge.vector_store import get_vector_store, VectorStoreType
            
            # Chunk document
            chunks = await chunking_pipeline.chunk_document(document, str(document.processed_content), db=db)
            
            # Generate embeddings
            embeddings = await embedding_pipeline.process_document_embeddings(
                chunks,
                document.embedding_provider
            )
            
            # Add to vector store
            vector_store = get_vector_store(VectorStoreType.PGVECTOR)
            await vector_store.add_embeddings(embeddings)
            
            document.status = KnowledgeDocumentStatus.INDEXED
            document.indexed_at = func.now()
            await db.commit()
            
            logger.info(f"Document {document_id} indexed successfully")
            return {"status": "success", "document_id": document_id, "chunk_count": len(chunks)}
    
    return asyncio.run(_index())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.document_tasks.cleanup_old_documents')
def cleanup_old_documents(self) -> dict:
    """
    Cleanup old documents (scheduled task)
    
    Returns:
        Cleanup result
    """
    import asyncio
    
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            # Delete documents older than 90 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            result = await db.execute(
                select(Document).where(
                    Document.created_at < cutoff_date,
                    Document.status == DocumentStatus.ARCHIVED
                )
            )
            documents = result.scalars().all()
            
            count = 0
            for doc in documents:
                doc.deleted_at = datetime.now(timezone.utc)
                count += 1
            
            await db.commit()
            
            logger.info(f"Cleaned up {count} old documents")
            return {"status": "success", "cleaned_count": count}
    
    return asyncio.run(_cleanup())
