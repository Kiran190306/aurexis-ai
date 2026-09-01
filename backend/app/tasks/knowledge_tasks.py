"""
Knowledge Management Tasks
Celery tasks for asynchronous knowledge base operations, embedding generation, and RAG preparation
"""
from celery import Task
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.worker import celery_app
from app.core.database import AsyncSessionLocal
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk, DocumentStatus


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


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.knowledge_tasks.generate_embeddings')
def generate_embeddings(self, document_id: int) -> dict:
    """
    Generate embeddings for a document asynchronously
    
    Args:
        document_id: Document ID to generate embeddings for
        
    Returns:
        Embedding generation result
    """
    import asyncio
    from app.knowledge.chunking import chunking_pipeline
    from app.knowledge.embeddings import embedding_pipeline
    from app.knowledge.vector_store import get_vector_store, VectorStoreType
    from app.models.knowledge import DocumentStatus
    
    async def _generate():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Knowledge document {document_id} not found")
                return {"status": "error", "message": "Document not found"}
            
            # Check if already indexed
            if document.status == DocumentStatus.INDEXED:
                logger.info(f"Document {document_id} already indexed")
                return {"status": "success", "document_id": document_id, "already_indexed": True}
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await db.commit()
            
            try:
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
                
                # Update document status to indexed
                document.status = DocumentStatus.INDEXED
                document.indexed_at = func.now()
                await db.commit()
                
                logger.info(f"Embeddings generated and indexed for document {document_id}")
                return {
                    "status": "success",
                    "document_id": document_id,
                    "chunk_count": len(chunks),
                    "embedding_count": len(embeddings)
                }
            except Exception as e:
                logger.error(f"Failed to generate embeddings for document {document_id}: {e}", exc_info=True)
                document.status = DocumentStatus.FAILED
                await db.commit()
                return {"status": "error", "message": str(e), "document_id": document_id}
    
    return asyncio.run(_generate())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.knowledge_tasks.reindex_document')
def reindex_document(self, document_id: int) -> dict:
    """
    Re-index a document with new embedding model
    
    Args:
        document_id: Document ID to re-index
        
    Returns:
        Re-indexing result
    """
    import asyncio
    
    async def _reindex():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Knowledge document {document_id} not found")
                return {"status": "error", "message": "Document not found"}
            
            # Re-index document with new embeddings
            from app.knowledge.chunking import chunking_pipeline
            from app.knowledge.embeddings import embedding_pipeline
            from app.knowledge.vector_store import get_vector_store, VectorStoreType
            
            # Delete existing chunks
            chunk_result = await db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
            )
            chunks = chunk_result.scalars().all()
            for chunk in chunks:
                await db.delete(chunk)
            
            # Regenerate chunks and embeddings
            new_chunks = await chunking_pipeline.chunk_document(document, str(document.processed_content), db=db)
            embeddings = await embedding_pipeline.process_document_embeddings(
                new_chunks,
                document.embedding_provider
            )
            
            # Update vector store
            vector_store = get_vector_store(VectorStoreType.PGVECTOR)
            await vector_store.delete_document(document_id)
            await vector_store.add_embeddings(embeddings)
            
            document.status = DocumentStatus.INDEXED
            document.indexed_at = func.now()
            await db.commit()
            
            logger.info(f"Document {document_id} re-indexed successfully")
            return {"status": "success", "document_id": document_id, "chunk_count": len(new_chunks)}
    
    return asyncio.run(_reindex())


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.knowledge_tasks.update_vector_index')
def update_vector_index(self) -> dict:
    """
    Update vector index (scheduled task)
    
    Returns:
        Update result
    """
    import asyncio
    
    async def _update():
        # Update vector index - optimize and rebuild if needed
        from app.knowledge.vector_store import get_vector_store, VectorStoreType
        
        vector_store = get_vector_store(VectorStoreType.PGVECTOR)
        await vector_store.optimize_index()
        
        logger.info("Vector index updated successfully")
        return {"status": "success"}
    
    return asyncio.run(_update())
