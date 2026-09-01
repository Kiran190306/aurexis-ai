# Enterprise Knowledge Platform & RAG Architecture

**Epic:** EPIC-015
**Version:** Jarvis AI v1.2
**Date:** August 5, 2026

## Overview

The Enterprise Knowledge Platform is a production-grade Retrieval-Augmented Generation (RAG) system that serves as the primary knowledge repository for Jarvis AI. It enables intelligent document ingestion, semantic search, and context-aware responses through a multi-stage pipeline.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Knowledge Platform                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Document Ingestion Layer                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   PDF    │ │  DOCX    │ │  PPTX    │ │ Markdown │ │   TXT    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   HTML   │ │   CSV    │ │   JSON   │ │   XML    │ │   OCR    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐                                                                    │
│  │   ZIP    │ (Multi-file archives)                                            │
│  └──────────┘                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Document Processing Layer                                  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Metadata Extractor│ │ Language Detector │ │ Checksum Validator│           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Duplicate Detector│ │ Version Tracker   │ │ Lifecycle Manager │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Chunking Pipeline                                      │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Semantic Chunking│ │Recursive Chunking│ │ Sliding Window   │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Parent/Child     │ │ Adaptive Size    │ │ Metadata Preserv │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Embedding Pipeline                                      │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ BAAI bge-large   │ │ multilingual-e5  │ │  OpenAI Embed    │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │  Jina Embeddings │ │ Batch Generator  │ │  Embedding Cache │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Vector Database Abstraction Layer                           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │    pgvector      │ │    ChromaDB      │ │     Qdrant       │           │
│  │    (Primary)     │ │    (Optional)    │ │    (Optional)    │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│                              │                                               │
│                    ┌─────────┴─────────┐                                     │
│                    │  Vector Store API │                                     │
│                    └───────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Hybrid Retrieval Layer                                 │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │      BM25        │ │  Dense Retrieval │ │  Hybrid Ranking  │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Metadata Filter  │ │   Tag Filter     │ │  Date Filter     │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐                                     │
│  │ Score Normaliz.  │ │  Result Merge    │                                     │
│  └──────────────────┘ └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Reranking Layer                                      │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │  Cross Encoder   │ │ Context Optimize │ │ Duplicate Remove │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐                                                              │
│  │ Result Diversify│                                                              │
│  └──────────────────┘                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Context Builder Layer                                   │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Token Budgeting  │ │  Auto Compress   │ │ Source Attribut. │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐                                     │
│  │ Citation Generate│ │ Confidence Score │                                     │
│  └──────────────────┘ └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agent Integration Layer                                   │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │  Planner Agent   │ │ Knowledge Agent  │ │   Retriever      │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │     Reranker     │ │ Context Builder  │ │      LLM         │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐                                                              │
│  │ Reflection Agent │                                                              │
│  └──────────────────┘                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Document Ingestion Layer

**Purpose:** Accept and validate documents from multiple sources

**Supported Formats:**
- PDF (text and OCR)
- DOCX (Microsoft Word)
- PPTX (Microsoft PowerPoint)
- Markdown (.md)
- Plain Text (.txt)
- HTML
- CSV
- JSON
- XML
- Images (PNG, JPG, etc. via OCR)
- ZIP archives (multi-file upload)

**Key Components:**
- File type detection
- Size validation
- Content validation
- Virus scanning hook
- Permission check

### 2. Document Processing Layer

**Purpose:** Extract metadata, detect duplicates, and track document versions

**Components:**

**Metadata Extractor:**
- Title extraction
- Author extraction
- Creation date
- Modification date
- File size
- Page count
- Word count
- Language detection

**Language Detector:**
- FastText-based language identification
- Confidence scoring
- Multi-language document support

**Checksum Validator:**
- SHA-256 hash generation
- Content integrity verification
- Duplicate detection

**Duplicate Detector:**
- Content-based deduplication
- Fuzzy matching
- Near-duplicate detection

**Version Tracker:**
- Document versioning
- Change tracking
- Rollback capability

**Lifecycle Manager:**
- Document status (processing, indexed, archived, deleted)
- Retention policies
- Automatic cleanup

### 3. Chunking Pipeline

**Purpose:** Split documents into semantically meaningful chunks

**Strategies:**

**Semantic Chunking:**
- Sentence boundary detection
- Paragraph preservation
- Topic segmentation
- NLP-based splitting

**Recursive Chunking:**
- Hierarchical document structure
- Header-based splitting
- Nested chunking

**Sliding Window:**
- Overlapping chunks
- Configurable window size
- Configurable overlap

**Parent/Child Chunks:**
- Large parent chunks for context
- Smaller child chunks for retrieval
- Parent-child linking

**Adaptive Chunking:**
- Dynamic chunk size based on content
- Content-aware splitting
- Density-based chunking

**Metadata Preservation:**
- Chunk-level metadata
- Source document reference
- Position information

### 4. Embedding Pipeline

**Purpose:** Generate vector representations for chunks

**Supported Providers:**

**BAAI bge-large-en-v1.5:**
- High-quality English embeddings
- 1024 dimensions
- Local deployment option

**multilingual-e5-large:**
- Multi-language support
- 1024 dimensions
- Cross-lingual retrieval

**OpenAI Embeddings:**
- text-embedding-3-small
- text-embedding-3-large
- API-based

**Jina Embeddings:**
- jina-embeddings-v2-base-en
- jina-embeddings-v2-base-de
- Local deployment option

**Features:**
- Configurable provider selection
- Batch embedding generation
- Embedding cache (Redis)
- Fallback providers
- Rate limiting
- Error handling

### 5. Vector Database Abstraction Layer

**Purpose:** Provide unified interface for multiple vector databases

**Primary: pgvector (PostgreSQL)**
- Native PostgreSQL extension
- ACID compliance
- SQL-based queries
- Existing infrastructure integration

**Optional: ChromaDB**
- Standalone vector database
- Metadata filtering
- Collection management

**Optional: Qdrant**
- High performance
- Advanced filtering
- Distributed deployment

**Abstraction API:**
```python
class VectorStore(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        top_k: int, 
        filters: Dict[str, Any]
    ) -> List[SearchResult]:
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        pass
```

### 6. Hybrid Retrieval Layer

**Purpose:** Combine keyword and semantic search for optimal results

**Components:**

**BM25 (Keyword Search):**
- Elasticsearch integration
- Term frequency analysis
- Document frequency
- Relevance scoring

**Dense Retrieval (Vector Search):**
- Cosine similarity
- Euclidean distance
- Dot product similarity

**Hybrid Ranking:**
- Score fusion (weighted average)
- Reciprocal rank fusion
- Learning to rank

**Filtering:**
- Metadata filtering
- Tag filtering
- Date range filtering
- User permission filtering

**Score Normalization:**
- Min-max normalization
- Z-score normalization
- Rank normalization

**Result Merge:**
- Deduplication
- Relevance balancing
- Diversity promotion

### 7. Reranking Layer

**Purpose:** Improve retrieval quality through advanced reranking

**Components:**

**Cross Encoder:**
- BAAI bge-reranker-large
- Cohere Rerank API
- MS MARCO models
- Pairwise relevance scoring

**Context Optimization:**
- Redundancy removal
- Information density optimization
- Query-context alignment

**Duplicate Removal:**
- Near-duplicate detection
- Content deduplication
- Semantic deduplication

**Result Diversification:**
- Maximal marginal relevance (MMR)
- Clustering-based diversity
- Category balancing

### 8. Context Builder Layer

**Purpose:** Build optimal context for LLM generation

**Components:**

**Token Budgeting:**
- Dynamic token allocation
- Per-chunk token estimation
- Context window management

**Automatic Compression:**
- Summarization
- Information extraction
- Key point extraction

**Source Attribution:**
- Citation generation
- Reference linking
- Confidence scoring

**Confidence Scoring:**
- Retrieval confidence
- Source reliability
- Temporal relevance

### 9. Agent Integration Layer

**Purpose:** Integrate RAG with multi-agent architecture

**Planner Agent:**
- Query decomposition
- Retrieval planning
- Multi-step reasoning

**Knowledge Agent:**
- Retrieval orchestration
- Result synthesis
- Answer generation

**Retriever:**
- Query expansion
- Multi-hop retrieval
- Iterative refinement

**Reranker:**
- Result quality assessment
- Relevance calibration
- Confidence estimation

**Context Builder:**
- Context assembly
- Information ordering
- Citation formatting

**LLM:**
- Response generation
- Answer synthesis
- Citation integration

**Reflection Agent:**
- Answer quality assessment
- Fact verification
- Consistency checking

## Security Layer

### File Validation
- File type verification
- Content sanitization
- Size limits
- Format validation

### Virus Scanning Hook
- Integration with antivirus APIs
- Quarantine mechanism
- Scan result logging

### Permission-Aware Retrieval
- User-based access control
- Document-level permissions
- Role-based filtering

### Encrypted Storage
- At-rest encryption
- In-transit encryption
- Key management

### Audit Logs
- Access logging
- Modification tracking
- Compliance reporting

## API Endpoints

### Document Management
- `POST /knowledge/upload` - Upload documents
- `POST /knowledge/index` - Trigger indexing
- `GET /knowledge/documents` - List documents
- `GET /knowledge/document/{id}` - Get document details
- `DELETE /knowledge/document/{id}` - Delete document

### Search & Query
- `POST /knowledge/search` - Semantic search
- `POST /knowledge/query` - RAG query with context

### Administration
- `GET /knowledge/status` - Indexing status
- `GET /knowledge/statistics` - Embedding statistics
- `POST /knowledge/reindex` - Rebuild index

## Frontend Components

### Knowledge Dashboard
- Document overview
- Upload manager
- Indexing progress
- Search interface

### Upload Manager
- Drag-and-drop upload
- Batch upload
- Progress tracking
- Error handling

### Indexing Status
- Real-time progress
- Error reporting
- Queue management

### Search Interface
- Query input
- Filter controls
- Result display
- Citation viewer

### Citation Viewer
- Source highlighting
- Reference linking
- Confidence display

### Knowledge Graph
- Document relationships
- Topic clustering
- Visual exploration

### Embedding Statistics
- Storage metrics
- Retrieval performance
- Quality metrics

## Database Schema

### Documents Table
```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(500),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    language VARCHAR(10),
    status VARCHAR(20) NOT NULL,
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES knowledge_documents(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP,
    deleted_at TIMESTAMP
);
```

### Document Chunks Table
```sql
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES knowledge_documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Embeddings Table (pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_embeddings (
    id UUID PRIMARY KEY,
    chunk_id UUID NOT NULL REFERENCES knowledge_chunks(id),
    embedding vector(1024) NOT NULL,
    embedding_provider VARCHAR(50),
    embedding_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_embeddings_embedding 
ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### Search History Table
```sql
CREATE TABLE knowledge_search_history (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    results JSONB,
    result_count INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Performance Considerations

### Scalability
- Horizontal scaling of ingestion workers
- Vector database sharding
- Caching strategies
- Connection pooling

### Latency
- Embedding caching
- Pre-computed embeddings
- Query optimization
- Result caching

### Throughput
- Batch processing
- Parallel embedding generation
- Asynchronous indexing
- Queue-based processing

## Monitoring & Observability

### Metrics
- Ingestion rate
- Indexing latency
- Search latency
- Retrieval accuracy
- Cache hit rate

### Logging
- Document processing logs
- Search query logs
- Error logs
- Performance logs

### Alerts
- Ingestion failures
- Indexing errors
- Performance degradation
- Storage capacity

## Backward Compatibility

### Existing Systems
- PostgreSQL memory system remains unchanged
- Existing API endpoints preserved
- Current agent architecture maintained
- Frontend components enhanced, not replaced

### Migration Path
- Gradual rollout of new features
- Feature flags for new functionality
- Data migration scripts
- Rollback procedures
