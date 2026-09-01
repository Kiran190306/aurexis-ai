"""
Vector Database Abstraction Layer
Supports pgvector (PostgreSQL), ChromaDB, Qdrant
"""
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger

from app.models.knowledge import (
    KnowledgeEmbedding,
    KnowledgeChunk,
    KnowledgeDocument,
    VectorStoreType,
)


@dataclass
class SearchResult:
    """Search result with metadata"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    metadata: Dict[str, Any]
    document_title: Optional[str] = None
    document_uuid: Optional[str] = None


class BaseVectorStore(ABC):
    """Base class for vector store implementations"""
    
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
    
    @abstractmethod
    async def add_embeddings(
        self,
        embeddings: List[KnowledgeEmbedding]
    ) -> None:
        """
        Add embeddings to vector store
        
        Args:
            embeddings: List of KnowledgeEmbedding instances
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult instances
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: int) -> None:
        """
        Delete all embeddings for a document
        
        Args:
            document_id: Document ID
        """
        pass
    
    @abstractmethod
    async def delete_chunk(self, chunk_id: int) -> None:
        """
        Delete embedding for a chunk
        
        Args:
            chunk_id: Chunk ID
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics
        
        Returns:
            Dictionary with statistics
        """
        pass


class PgVectorStore(BaseVectorStore):
    """
    PostgreSQL with pgvector extension
    Primary vector store implementation
    """
    
    def __init__(self, dimension: int = 1024):
        super().__init__(dimension)
        self._extension_checked = False
    
    def _ensure_extension(self) -> None:
        """Ensure pgvector extension is installed"""
        from app.core.database import get_db
        import asyncio
        from sqlalchemy import text
        
        async def check_extension() -> None:
            async for db in get_db():
                try:
                    await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    await db.commit()
                    logger.info("pgvector extension ensured")
                except Exception as e:
                    logger.error(f"Failed to ensure pgvector extension: {e}")
        
        # Run in background
        asyncio.create_task(check_extension())
    
    async def add_embeddings(
        self,
        embeddings: List[KnowledgeEmbedding]
    ) -> None:
        """
        Add embeddings to PostgreSQL with pgvector
        
        Args:
            embeddings: List of KnowledgeEmbedding instances
        """
        from app.core.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            for embedding in embeddings:
                # Convert embedding list to JSON string for PostgreSQL
                import json
                embedding_json = json.dumps(embedding.embedding)
                
                try:
                    # Insert embedding (no upsert since chunk_id is not unique)
                    query = text("""
                        INSERT INTO knowledge_embeddings 
                        (chunk_id, document_id, embedding, embedding_dimension, 
                         embedding_provider, embedding_model, cache_key)
                        VALUES (:chunk_id, :document_id, :embedding, 
                                :dimension, :provider, :model, :cache_key)
                    """)
                    
                    await db.execute(query, {
                        'chunk_id': embedding.chunk_id,
                        'document_id': embedding.document_id,
                        'embedding': embedding_json,
                        'dimension': embedding.embedding_dimension,
                        'provider': embedding.embedding_provider.value,
                        'model': embedding.embedding_model,
                        'cache_key': embedding.cache_key
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to add embedding {embedding.id}: {e}")
                    raise
            
            await db.commit()
            logger.info(f"Added {len(embeddings)} embeddings to pgvector")
            return
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search using pgvector cosine similarity
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            List of SearchResult instances
        """
        from app.core.database import get_db
        from sqlalchemy import text, select, bindparam
        from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
        
        async for db in get_db():
            vector_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Build query with filters using bindparam
            where_clauses = []
            params = {'vector': vector_str, 'top_k': top_k}
            
            if filters:
                if 'user_id' in filters:
                    where_clauses.append("kd.user_id = :user_id")
                    params['user_id'] = filters['user_id']
                
                if 'language' in filters:
                    where_clauses.append("kd.language = :language")
                    params['language'] = filters['language']
                
                if 'document_type' in filters:
                    where_clauses.append("kd.document_type = :doc_type")
                    params['doc_type'] = filters['document_type']
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Filter out embeddings with dimension 0 (empty arrays)
            where_sql += " AND ke.embedding_dimension > 0"
            
            # Use bindparam for the vector cast - cast JSON to text then to vector
            query = text(f"""
                SELECT 
                    kc.id as chunk_id,
                    kc.document_id,
                    kc.content,
                    kc.metadata_json,
                    kd.title as document_title,
                    kd.uuid as document_uuid,
                    1 - (ke.embedding::text::vector <=> cast(:vector as vector)) as score
                FROM knowledge_embeddings ke
                JOIN knowledge_chunks kc ON ke.chunk_id = kc.id
                JOIN knowledge_documents kd ON kc.document_id = kd.id
                WHERE {where_sql}
                ORDER BY ke.embedding::text::vector <=> cast(:vector as vector)
                LIMIT :top_k
            """)
            
            result = await db.execute(query, params)
            rows = result.fetchall()
            
            search_results = []
            for row in rows:
                search_results.append(SearchResult(
                    chunk_id=row.chunk_id,
                    document_id=row.document_id,
                    content=row.content,
                    score=float(row.score),
                    metadata=row.metadata_json or {},
                    document_title=row.document_title,
                    document_uuid=str(row.document_uuid) if row.document_uuid else None
                ))
            
            logger.info(f"pgvector search returned {len(search_results)} results")
            return search_results
        
        return []
    
    async def delete_document(self, document_id: int) -> None:
        """Delete all embeddings for a document"""
        from app.core.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            query = text("""
                DELETE FROM knowledge_embeddings 
                WHERE document_id = :document_id
            """)
            await db.execute(query, {'document_id': document_id})
            await db.commit()
            logger.info(f"Deleted embeddings for document {document_id}")
    
    async def delete_chunk(self, chunk_id: int) -> None:
        """Delete embedding for a chunk"""
        from app.core.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            query = text("""
                DELETE FROM knowledge_embeddings 
                WHERE chunk_id = :chunk_id
            """)
            await db.execute(query, {'chunk_id': chunk_id})
            await db.commit()
            logger.info(f"Deleted embedding for chunk {chunk_id}")
            return
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pgvector statistics"""
        from app.core.database import get_db
        from sqlalchemy import text
        
        async for db in get_db():
            # Count total embeddings
            count_query = text("SELECT COUNT(*) FROM knowledge_embeddings")
            result = await db.execute(count_query)
            total_embeddings = result.scalar()
            
            # Count unique documents
            doc_query = text("SELECT COUNT(DISTINCT document_id) FROM knowledge_embeddings")
            result = await db.execute(doc_query)
            total_documents = result.scalar()
            
            return {
                'total_embeddings': total_embeddings,
                'total_documents': total_documents,
                'dimension': self.dimension,
                'store_type': 'pgvector'
            }
        
        return {
            'total_embeddings': 0,
            'total_documents': 0,
            'dimension': self.dimension,
            'store_type': 'pgvector'
        }


class ChromaDBStore(BaseVectorStore):
    """
    ChromaDB vector store (optional)
    """
    
    def __init__(self, dimension: int = 1024, collection_name: str = "jarvis_knowledge"):
        super().__init__(dimension)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize ChromaDB client"""
        try:
            import chromadb
            self.client = chromadb.Client()
            if self.client:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"dimension": str(self.dimension)}
                )
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_embeddings(
        self,
        embeddings: List[KnowledgeEmbedding]
    ) -> None:
        """Add embeddings to ChromaDB"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")
        
        ids = []
        vectors = []
        metadatas = []
        
        for emb in embeddings:
            ids.append(str(emb.chunk_id))
            vectors.append(emb.embedding)
            metadatas.append({
                'document_id': emb.document_id,
                'embedding_provider': emb.embedding_provider.value,
                'embedding_model': emb.embedding_model,
            })
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas
            )
            logger.info(f"Added {len(embeddings)} embeddings to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add embeddings to ChromaDB: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search ChromaDB"""
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            search_results = []
            for idx, chunk_id in enumerate(results['ids'][0]):
                search_results.append(SearchResult(
                    chunk_id=int(chunk_id),
                    document_id=results['metadatas'][0][idx]['document_id'],
                    content="",  # Would need to fetch from database
                    score=1 - results['distances'][0][idx],  # Convert distance to similarity
                    metadata=results['metadatas'][0][idx]
                ))
            
            logger.info(f"ChromaDB search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            raise
    
    async def delete_document(self, document_id: int) -> None:
        """Delete document embeddings from ChromaDB"""
        if not self.collection:
            return
        
        try:
            # Get all chunk IDs for document
            from app.core.database import get_db
            from sqlalchemy import select
            from app.models.knowledge import KnowledgeChunk
            
            async for db in get_db():
                result = await db.execute(
                    select(KnowledgeChunk.id).where(
                        KnowledgeChunk.document_id == document_id
                    )
                )
                chunk_ids = [str(row[0]) for row in result.fetchall()]
                
                if chunk_ids:
                    self.collection.delete(ids=chunk_ids)
                    logger.info(f"Deleted {len(chunk_ids)} embeddings from ChromaDB")
        except Exception as e:
            logger.error(f"Failed to delete from ChromaDB: {e}")
    
    async def delete_chunk(self, chunk_id: int) -> None:
        """Delete chunk embedding from ChromaDB"""
        if not self.collection:
            return
        
        try:
            self.collection.delete(ids=[str(chunk_id)])
            logger.info(f"Deleted embedding {chunk_id} from ChromaDB")
        except Exception as e:
            logger.error(f"Failed to delete from ChromaDB: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics"""
        if not self.collection:
            return {'store_type': 'chromadb', 'error': 'not_initialized'}
        
        try:
            count = self.collection.count()
            return {
                'total_embeddings': count,
                'collection_name': self.collection_name,
                'dimension': self.dimension,
                'store_type': 'chromadb'
            }
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {'store_type': 'chromadb', 'error': str(e)}


class QdrantStore(BaseVectorStore):
    """
    Qdrant vector store (optional)
    """
    
    def __init__(self, dimension: int = 1024, collection_name: str = "jarvis_knowledge"):
        super().__init__(dimension)
        self.collection_name = collection_name
        self.client = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            
            self.client = QdrantClient(url="http://localhost:6333")
            
            # Create collection if not exists
            from qdrant_client.models import CreateCollection
            
            if self.client:
                try:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.dimension,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {self.collection_name}")
                except Exception:
                    # Collection might already exist
                    pass
            
            logger.info("Qdrant initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            self.client = None
    
    async def add_embeddings(
        self,
        embeddings: List[KnowledgeEmbedding]
    ) -> None:
        """Add embeddings to Qdrant"""
        if not self.client:
            raise RuntimeError("Qdrant not initialized")
        
        from qdrant_client.models import PointStruct
        
        points = []
        for emb in embeddings:
            points.append(PointStruct(
                id=emb.chunk_id,
                vector=emb.embedding,
                payload={
                    'document_id': emb.document_id,
                    'embedding_provider': emb.embedding_provider.value,
                    'embedding_model': emb.embedding_model,
                }
            ))
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(embeddings)} embeddings to Qdrant")
        except Exception as e:
            logger.error(f"Failed to add embeddings to Qdrant: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search Qdrant"""
        if not self.client:
            raise RuntimeError("Qdrant not initialized")
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        search_filter = None
        if filters:
            conditions = []
            if 'document_id' in filters:
                conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filters['document_id'])
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter
            )
            
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    chunk_id=result.id,
                    document_id=result.payload.get('document_id'),
                    content="",
                    score=result.score,
                    metadata=result.payload
                ))
            
            logger.info(f"Qdrant search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise
    
    async def delete_document(self, document_id: int) -> None:
        """Delete document embeddings from Qdrant"""
        if not self.client:
            return
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted embeddings for document {document_id} from Qdrant")
        except Exception as e:
            logger.error(f"Failed to delete from Qdrant: {e}")
    
    async def delete_chunk(self, chunk_id: int) -> None:
        """Delete chunk embedding from Qdrant"""
        if not self.client:
            return
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[chunk_id]
            )
            logger.info(f"Deleted embedding {chunk_id} from Qdrant")
        except Exception as e:
            logger.error(f"Failed to delete from Qdrant: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant statistics"""
        if not self.client:
            return {'store_type': 'qdrant', 'error': 'not_initialized'}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                'total_embeddings': collection_info.points_count,
                'collection_name': self.collection_name,
                'dimension': self.dimension,
                'store_type': 'qdrant'
            }
        except Exception as e:
            logger.error(f"Failed to get Qdrant stats: {e}")
            return {'store_type': 'qdrant', 'error': str(e)}


class VectorStoreFactory:
    """
    Factory for creating vector store instances
    """
    
    @staticmethod
    def create_store(
        store_type: VectorStoreType,
        dimension: int = 1024,
        **kwargs: Any
    ) -> BaseVectorStore:
        """
        Create vector store instance
        
        Args:
            store_type: VectorStoreType enum
            dimension: Embedding dimension
            **kwargs: Additional store-specific parameters
            
        Returns:
            Vector store instance
        """
        if store_type == VectorStoreType.PGVECTOR:
            return PgVectorStore(dimension=dimension)
        elif store_type == VectorStoreType.CHROMADB:
            return ChromaDBStore(dimension=dimension, **kwargs)
        elif store_type == VectorStoreType.QDRANT:
            return QdrantStore(dimension=dimension, **kwargs)
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")


# Singleton instance for default store
def get_vector_store(store_type: VectorStoreType = VectorStoreType.PGVECTOR) -> BaseVectorStore:
    """Get vector store instance"""
    return VectorStoreFactory.create_store(store_type)
