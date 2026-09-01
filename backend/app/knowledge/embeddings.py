"""
Embedding Pipeline
Multiple providers (BAAI bge, multilingual-e5, OpenAI, Jina), batch generation, cache
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import hashlib
import json

from loguru import logger

from app.models.knowledge import (
    KnowledgeEmbedding,
    KnowledgeChunk,
    EmbeddingProvider,
)
from app.core.config import settings


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers"""
    
    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self.dimension = dimension
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        pass
    
    def get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        content = f"{self.model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()


class BAAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    BAAI bge-large-en-v1.5 embedding provider
    Local deployment option
    """
    
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5", dimension: int = 1024):
        super().__init__(model_name, dimension)
        self.model = None
    
    def _load_model(self) -> None:
        """Load BAAI model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded BAAI model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load BAAI model: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self.model:
            self._load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            self._load_model()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class MultilingualE5Provider(BaseEmbeddingProvider):
    """
    multilingual-e5-large embedding provider
    Cross-lingual support
    """
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large", dimension: int = 1024):
        super().__init__(model_name, dimension)
        self.model = None
    
    def _load_model(self) -> None:
        """Load E5 model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded E5 model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load E5 model: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self.model:
            self._load_model()
        
        # E5 requires "query: " or "passage: " prefix
        prefixed_text = f"passage: {text}"
        embedding = self.model.encode(prefixed_text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            self._load_model()
        
        prefixed_texts = [f"passage: {t}" for t in texts]
        embeddings = self.model.encode(prefixed_texts, convert_to_numpy=True)
        return embeddings.tolist()


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider
    API-based
    """
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536
    ):
        super().__init__(model_name, dimension)
        self.client: Optional[Any] = None
        self._load_client()
    
    def _load_client(self) -> None:
        """Load OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"Loaded OpenAI client: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load OpenAI client: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self.client:
            raise RuntimeError("Client not loaded")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return list(response.data[0].embedding)
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.client:
            raise RuntimeError("Client not loaded")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise


class JinaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Jina embedding provider
    Local deployment option
    """
    
    def __init__(self, model_name: str = "jinaai/jina-embeddings-v2-base-en", dimension: int = 768):
        super().__init__(model_name, dimension)
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Jina model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
            logger.info(f"Loaded Jina model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load Jina model: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if not self.model:
            self._load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            self._load_model()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class EmbeddingCache:
    """
    Redis-based embedding cache
    """
    
    def __init__(self) -> None:
        self.redis_client: Optional[Any] = None
        self._load_redis()
    
    def _load_redis(self) -> None:
        """Load Redis client"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(settings.REDIS_URL)
            logger.info("Embedding cache connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
    
    async def get(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(f"embedding:{cache_key}")
            if cached:
                loaded = json.loads(cached)
                if isinstance(loaded, list):
                    return loaded
            return None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None
    
    async def set(self, cache_key: str, embedding: List[float], ttl: int = 86400) -> None:
        """Set embedding in cache"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                f"embedding:{cache_key}",
                ttl,
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def delete(self, cache_key: str) -> None:
        """Delete embedding from cache"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(f"embedding:{cache_key}")
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")


class EmbeddingPipeline:
    """
    Main embedding pipeline with provider selection, caching, and batch processing
    """
    
    def __init__(self) -> None:
        self.providers: Dict[EmbeddingProvider, Any] = {
            EmbeddingProvider.BAAI_BGE: BAAIEmbeddingProvider,
            EmbeddingProvider.MULTILINGUAL_E5: MultilingualE5Provider,
            EmbeddingProvider.OPENAI: OpenAIEmbeddingProvider,
            EmbeddingProvider.JINA: JinaEmbeddingProvider,
        }
        self.cache = EmbeddingCache()
        self.default_provider = EmbeddingProvider.BAAI_BGE
    
    def get_provider(
        self,
        provider: Optional[EmbeddingProvider] = None,
        model_name: Optional[str] = None
    ) -> BaseEmbeddingProvider:
        """
        Get embedding provider instance
        
        Args:
            provider: Provider enum
            model_name: Optional model name override
            
        Returns:
            Provider instance
        """
        provider = provider or self.default_provider
        provider_class = self.providers.get(provider, BAAIEmbeddingProvider)
        
        if model_name:
            # Determine dimension based on model
            if "small" in model_name:
                dimension = 1536
            elif "large" in model_name:
                dimension = 1024
            else:
                dimension = 768
            return provider_class(model_name=model_name, dimension=dimension)  # type: ignore
        
        return provider_class()  # type: ignore
    
    async def embed_chunk(
        self,
        chunk: KnowledgeChunk,
        provider: Optional[EmbeddingProvider] = None
    ) -> List[float]:
        """
        Generate embedding for a single chunk with caching
        
        Args:
            chunk: KnowledgeChunk instance
            provider: Optional provider override
            
        Returns:
            Embedding vector
        """
        provider_instance = self.get_provider(provider)
        cache_key = provider_instance.get_cache_key(str(chunk.content))
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Generate embedding
        embedding = await provider_instance.embed(str(chunk.content))
        
        # Cache result
        await self.cache.set(cache_key, embedding)
        
        return embedding
    
    async def embed_chunks_batch(
        self,
        chunks: List[KnowledgeChunk],
        provider: Optional[EmbeddingProvider] = None,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple chunks in batches
        
        Args:
            chunks: List of KnowledgeChunk instances
            provider: Optional provider override
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        provider_instance = self.get_provider(provider)
        embeddings: List[List[float]] = []
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [str(chunk.content) for chunk in batch]
            
            # Check cache for each
            cache_keys = [provider_instance.get_cache_key(text) for text in texts]
            cached_embeddings = [await self.cache.get(key) for key in cache_keys]
            
            # Separate cached and uncached
            uncached_indices = [i for i, emb in enumerate(cached_embeddings) if emb is None]
            uncached_texts = [texts[i] for i in uncached_indices]
            
            # Generate embeddings for uncached
            if uncached_texts:
                new_embeddings = await provider_instance.embed_batch(uncached_texts)
                
                # Cache new embeddings
                for idx, embedding in zip(uncached_indices, new_embeddings):
                    await self.cache.set(cache_keys[idx], embedding)
            
            # Combine results
            batch_embeddings: List[List[float]] = []
            for i, cached in enumerate(cached_embeddings):
                if cached is not None:
                    batch_embeddings.append(cached)
                else:
                    # Should have been filled in above
                    batch_embeddings.append([])  # Placeholder, should not happen
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def save_embeddings(
        self,
        chunks: List[KnowledgeChunk],
        embeddings: List[List[float]],
        provider: EmbeddingProvider,
        model_name: str
    ) -> List[KnowledgeEmbedding]:
        """
        Save embeddings to database
        
        Args:
            chunks: List of KnowledgeChunk instances
            embeddings: List of embedding vectors
            provider: Provider used
            model_name: Model name used
            
        Returns:
            List of KnowledgeEmbedding instances
        """
        from app.core.database import get_db
        
        async for db in get_db():
            knowledge_embeddings = []
            
            for chunk, embedding in zip(chunks, embeddings):
                cache_key = hashlib.sha256(
                    f"{model_name}:{chunk.content}".encode()
                ).hexdigest()
                
                knowledge_embedding = KnowledgeEmbedding(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    embedding=embedding,
                    embedding_dimension=len(embedding),
                    embedding_provider=provider,
                    embedding_model=model_name,
                    cache_key=cache_key
                )
                db.add(knowledge_embedding)
                knowledge_embeddings.append(knowledge_embedding)
            
            await db.commit()
            
            for ke in knowledge_embeddings:
                await db.refresh(ke)
            
            logger.info(f"Saved {len(knowledge_embeddings)} embeddings to database")
            return knowledge_embeddings
        
        return []
    
    async def process_document_embeddings(
        self,
        chunks: List[KnowledgeChunk],
        provider: Optional[EmbeddingProvider] = None
    ) -> List[KnowledgeEmbedding]:
        """
        Complete pipeline: generate and save embeddings for document chunks
        
        Args:
            chunks: List of KnowledgeChunk instances
            provider: Optional provider override
            
        Returns:
            List of KnowledgeEmbedding instances
        """
        provider = provider or self.default_provider
        provider_instance = self.get_provider(provider)
        
        # Generate embeddings
        embeddings = await self.embed_chunks_batch(chunks, provider)
        
        # Save to database
        knowledge_embeddings = await self.save_embeddings(
            chunks,
            embeddings,
            provider,
            provider_instance.model_name
        )
        
        return knowledge_embeddings


# Singleton instance
embedding_pipeline = EmbeddingPipeline()
