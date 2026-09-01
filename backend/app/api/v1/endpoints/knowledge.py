"""
Knowledge Platform API Endpoints
Document upload, indexing, search, query, and document management
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import func

from app.core.security import get_current_user_id
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import (
    KnowledgeDocument,
    KnowledgeChunk,
    DocumentStatus,
    DocumentType,
    ChunkingStrategy,
    EmbeddingProvider,
)
from app.knowledge.ingestion import document_ingestor, document_extractor
from app.knowledge.processing import document_processor
from app.knowledge.chunking import chunking_pipeline
from app.knowledge.embeddings import embedding_pipeline
from app.knowledge.vector_store import get_vector_store, VectorStoreType
from app.knowledge.search import get_hybrid_search_engine, SearchFilter
from app.knowledge.reranking import get_reranking_pipeline
from app.knowledge.context import get_context_builder
from app.knowledge.agent import KnowledgeAgent, RAGQuery, RAGResult, knowledge_agent
from app.ai.setup import get_ai_engine
from app.ai.base import Message
from app.models.file import File as FileModel, FileType


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    chunking_strategy: str = Form("semantic"),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    embedding_provider: str = Form("baai_bge"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload and process a document
    
    - **file**: Document file (PDF, DOCX, PPTX, MD, TXT, HTML, CSV, JSON, XML, ZIP)
    - **title**: Optional document title
    - **chunking_strategy**: Chunking strategy (semantic, recursive, sliding_window, parent_child, adaptive)
    - **chunk_size**: Chunk size in characters
    - **chunk_overlap**: Chunk overlap in characters
    - **embedding_provider**: Embedding provider (baai_bge, multilingual_e5, openai, jina)
    """
    try:
        # Validate and read file
        content, doc_type, checksum = await document_ingestor.validate_upload(file, user_id)
        
        # Create file record
        file_record = FileModel(
            user_id=user_id,
            filename=file.filename,
            original_filename=file.filename,
            file_type=FileType.DOCUMENT,
            mime_type=file.content_type or "text/plain",
            file_size=len(content),
            storage_path=f"uploads/{user_id}/{file.filename}"
        )
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        
        # Create document record
        document = await document_ingestor.create_document_record(
            file=file,
            content=content,
            doc_type=doc_type,
            checksum=checksum,
            user_id=user_id,
            file_record=file_record,
            title=title,
            db=db
        )
        
        # Process document
        document = await document_processor.process_document(document, content, db=db)
        
        # Update configuration
        document.chunking_strategy = ChunkingStrategy(chunking_strategy)  # type: ignore[assignment]
        document.chunk_size = chunk_size  # type: ignore[assignment]
        document.chunk_overlap = chunk_overlap  # type: ignore[assignment]
        document.embedding_provider = EmbeddingProvider(embedding_provider)  # type: ignore[assignment]
        await db.commit()
        
        # Queue Celery task for embedding generation
        from app.worker import celery_app
        task = celery_app.send_task(
            'app.tasks.knowledge_tasks.generate_embeddings',
            args=[document.id],
            queue='knowledge'
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "document_id": document.uuid,
                "task_id": task.id,
                "status": document.status.value,
                "message": "Document uploaded successfully, processing started"
            }
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/index/{document_uuid}")
async def index_document(
    document_uuid: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Trigger indexing for a document
    
    - **document_uuid**: Document UUID
    """
    try:
        # Get document
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.uuid == document_uuid,
                KnowledgeDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.status == DocumentStatus.INDEXED:
            return {"message": "Document already indexed"}
        
        # Queue Celery task for embedding generation
        from app.worker import celery_app
        task = celery_app.send_task(
            'app.tasks.knowledge_tasks.generate_embeddings',
            args=[document.id],
            queue='knowledge'
        )
        
        return {
            "document_id": document.uuid,
            "task_id": task.id,
            "status": "processing",
            "message": "Indexing task queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document indexing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search")
async def search_knowledge(
    query: str = Form(...),
    top_k: int = Form(10),
    use_hybrid: bool = Form(True),
    filters: Optional[str] = Form(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Search knowledge base
    
    - **query**: Search query
    - **top_k**: Number of results to return
    - **use_hybrid**: Use hybrid search (BM25 + dense)
    - **filters**: JSON string of filters (optional)
    """
    try:
        import json
        
        # Parse filters
        filter_dict = json.loads(filters) if filters else {}
        filter_dict['user_id'] = user_id
        
        # Get user chunks
        result = await db.execute(
            select(KnowledgeChunk).join(KnowledgeDocument).where(
                KnowledgeDocument.user_id == user_id,
                KnowledgeDocument.deleted_at.is_(None)
            )
        )
        chunks = result.scalars().all()
        
        # Get hybrid search engine and index chunks for BM25
        search_engine = get_hybrid_search_engine()
        if chunks:
            search_engine.index_chunks(list(chunks))
        
        # Search
        search_results: List[Any] = []
        if chunks:
            search_results = await search_engine.search(
                query=query,
                chunks=list(chunks),
                top_k=top_k,
                filters=filter_dict,
                use_hybrid=use_hybrid
            )
        
        # Format results
        formatted_results = []
        for r in search_results:
            formatted_results.append({
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "content": r.content,
                "score": r.score,
                "bm25_score": r.bm25_score,
                "dense_score": r.dense_score,
                "document_title": r.document_title,
                "document_uuid": r.document_uuid,
                "metadata": r.metadata
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "result_count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query")
async def rag_query(
    query: str = Form(...),
    top_k: int = Form(10),
    max_tokens: int = Form(4000),
    include_citations: bool = Form(True),
    user_id: int = Depends(get_current_user_id)
) -> dict[str, Any]:
    """
    RAG query with context building
    
    - **query**: Query text
    - **top_k**: Number of results to retrieve
    - **max_tokens**: Maximum tokens for context
    - **include_citations**: Include citations in response
    """
    try:
        # Build RAG query
        rag_query = RAGQuery(
            query=query,
            user_id=user_id,
            top_k=top_k,
            use_hybrid=True,
            max_tokens=max_tokens,
            include_citations=include_citations
        )
        
        # Execute RAG
        rag_result = await knowledge_agent.query(rag_query)
        
        # Generate answer using AI engine
        ai_engine = get_ai_engine()
        answer = None
        logger.info(f"Context text length: {len(rag_result.context.context_text) if rag_result.context.context_text else 0}")
        if rag_result.context.context_text:
            try:
                logger.info(f"Context text is present, preparing LLM generation")
                messages = [
                    Message(role="system", content="You are a helpful assistant. Answer the question based on the provided context. If the context doesn't contain the answer, say you don't know."),
                    Message(role="user", content=f"Context:\n{rag_result.context.context_text}\n\nQuestion: {query}")
                ]
                logger.info(f"Attempting LLM generation with {len(messages)} messages")
                llm_response = await ai_engine.generate(messages)
                answer = llm_response.content
                logger.info(f"LLM generation successful, answer length: {len(answer) if answer else 0}")
            except Exception as e:
                import traceback
                logger.error(f"LLM generation failed: {type(e).__name__}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning("Context text is empty, skipping LLM generation")
        
        # Format response
        return {
            "query": query,
            "answer": answer,
            "context": rag_result.context.context_text,
            "sources": rag_result.sources,
            "citations": [
                {
                    "document_title": c.document_title,
                    "document_uuid": c.document_uuid,
                    "page_number": c.page_number,
                    "confidence": c.confidence
                }
                for c in rag_result.context.citations
            ],
            "metadata": rag_result.metadata,
            "latency_ms": rag_result.latency_ms
        }
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    document_status: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    List user's documents
    
    - **skip**: Number of documents to skip
    - **limit**: Number of documents to return
    - **status**: Filter by status (optional)
    """
    try:
        query = select(KnowledgeDocument).where(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.deleted_at.is_(None)
        )
        
        if document_status:
            query = query.where(KnowledgeDocument.status == DocumentStatus(document_status))
        
        query = query.offset(skip).limit(limit)
        query = query.order_by(KnowledgeDocument.created_at.desc())
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        formatted_documents = []
        for doc in documents:
            formatted_documents.append({
                "uuid": doc.uuid,
                "title": doc.title,
                "file_name": doc.file_name,
                "document_type": doc.document_type.value,
                "status": doc.status.value,
                "chunk_count": doc.chunk_count,
                "token_count": doc.token_count,
                "created_at": doc.created_at.isoformat(),
                "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None
            })
        
        return {
            "documents": formatted_documents,
            "count": len(formatted_documents)
        }
        
    except Exception as e:
        logger.error(f"List documents failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/documents/{document_uuid}")
async def get_document(
    document_uuid: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get document details
    
    - **document_uuid**: Document UUID
    """
    try:
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.uuid == document_uuid,
                KnowledgeDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "uuid": document.uuid,
            "title": document.title,
            "file_name": document.file_name,
            "document_type": document.document_type.value,
            "status": document.status.value,
            "chunk_count": document.chunk_count,
            "token_count": document.token_count,
            "character_count": document.character_count,
            "language": document.language,
            "metadata": document.metadata_json,
            "chunking_strategy": document.chunking_strategy.value,
            "chunk_size": document.chunk_size,
            "chunk_overlap": document.chunk_overlap,
            "embedding_provider": document.embedding_provider.value if document.embedding_provider else None,
            "created_at": document.created_at.isoformat(),
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/documents/{document_uuid}")
async def delete_document(
    document_uuid: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Delete a document
    
    - **document_uuid**: Document UUID
    """
    try:
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.uuid == document_uuid,
                KnowledgeDocument.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Soft delete
        document.deleted_at = func.now()  # type: ignore[assignment]
        document.status = DocumentStatus.DELETED  # type: ignore[assignment]
        
        # Remove from vector store
        vector_store = get_vector_store(VectorStoreType.PGVECTOR)
        await vector_store.delete_document(int(document.id))
        
        await db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status")
async def get_knowledge_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get knowledge platform status
    """
    try:
        # Count documents
        doc_result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.user_id == user_id,
                KnowledgeDocument.deleted_at.is_(None)
            )
        )
        documents = doc_result.scalars().all()
        
        # Count chunks
        chunk_result = await db.execute(
            select(KnowledgeChunk).join(KnowledgeDocument).where(
                KnowledgeDocument.user_id == user_id,
                KnowledgeDocument.deleted_at.is_(None)
            )
        )
        chunks = chunk_result.scalars().all()
        
        # Get vector store stats
        vector_store = get_vector_store(VectorStoreType.PGVECTOR)
        vector_stats = await vector_store.get_stats()
        
        return {
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "indexed_count": sum(1 for d in documents if d.status == DocumentStatus.INDEXED),
            "processing_count": sum(1 for d in documents if d.status == DocumentStatus.PROCESSING),
            "vector_store_stats": vector_stats
        }
        
    except Exception as e:
        logger.error(f"Get status failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
