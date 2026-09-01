# Knowledge Platform API Documentation

**Version:** 1.0
**Base Path:** `/api/v1/knowledge`
**Authentication:** Bearer Token (JWT)

## Overview

The Knowledge Platform API provides endpoints for document management, ingestion, indexing, search, and RAG queries. All endpoints require authentication via JWT token.

## Authentication

All endpoints require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

The token is obtained from the authentication endpoint and represents the user identity.

## Endpoints

### Upload Document

Upload and process a document for the knowledge base.

**Endpoint:** `POST /knowledge/upload`

**Request:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Document file (PDF, DOCX, PPTX, MD, TXT, HTML, CSV, JSON, XML, ZIP) |
| title | string | No | Optional document title (defaults to filename) |
| chunking_strategy | string | No | Chunking strategy: `semantic`, `recursive`, `sliding_window`, `parent_child`, `adaptive` (default: `semantic`) |
| chunk_size | integer | No | Chunk size in characters (default: 1000) |
| chunk_overlap | integer | No | Chunk overlap in characters (default: 200) |
| embedding_provider | string | No | Embedding provider: `baai_bge`, `multilingual_e5`, `openai`, `jina` (default: `baai_bge`) |

**Response:** `201 Created`

```json
{
  "document_id": "uuid-string",
  "status": "processing",
  "message": "Document uploaded successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid file type or size
- `500 Internal Server Error`: Processing error

**Example:**

```bash
curl -X POST "https://api.jarvis.ai/api/v1/knowledge/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "chunking_strategy=semantic" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

---

### Index Document

Trigger indexing for a previously uploaded document.

**Endpoint:** `POST /knowledge/index/{document_uuid}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_uuid | string | Yes | Document UUID |

**Response:** `200 OK`

```json
{
  "document_id": "uuid-string",
  "status": "indexed",
  "chunk_count": 25,
  "embedding_count": 25
}
```

**Error Responses:**

- `404 Not Found`: Document not found
- `500 Internal Server Error`: Indexing error

**Example:**

```bash
curl -X POST "https://api.jarvis.ai/api/v1/knowledge/index/abc-123-def" \
  -H "Authorization: Bearer <token>"
```

---

### Search Knowledge Base

Search the knowledge base using hybrid search (BM25 + vector similarity).

**Endpoint:** `POST /knowledge/search`

**Request:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query text |
| top_k | integer | No | Number of results to return (default: 10) |
| use_hybrid | boolean | No | Use hybrid search (default: true) |
| filters | string | No | JSON string of filters (optional) |

**Response:** `200 OK`

```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "chunk_id": 123,
      "document_id": 456,
      "content": "Machine learning algorithms are...",
      "score": 0.95,
      "bm25_score": 0.82,
      "dense_score": 0.97,
      "document_title": "ML Guide",
      "document_uuid": "doc-uuid",
      "metadata": {
        "page_number": 5,
        "section": "Introduction"
      }
    }
  ],
  "result_count": 10
}
```

**Filter Format:**

```json
{
  "language": "en",
  "document_type": "pdf",
  "tags": ["machine learning", "algorithms"],
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

**Example:**

```bash
curl -X POST "https://api.jarvis.ai/api/v1/knowledge/search" \
  -H "Authorization: Bearer <token>" \
  -F "query=neural networks" \
  -F "top_k=5" \
  -F "use_hybrid=true"
```

---

### RAG Query

Execute a RAG query with context building and citations.

**Endpoint:** `POST /knowledge/query`

**Request:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Query text |
| top_k | integer | No | Number of results to retrieve (default: 10) |
| max_tokens | integer | No | Maximum tokens for context (default: 4000) |
| include_citations | boolean | No | Include citations in response (default: true) |

**Response:** `200 OK`

```json
{
  "query": "What is deep learning?",
  "context": "Deep learning is a subset of machine learning...",
  "sources": [
    {
      "chunk_id": 123,
      "document_id": 456,
      "document_title": "Deep Learning Guide",
      "document_uuid": "doc-uuid",
      "page_number": 10,
      "confidence": 0.95,
      "relevance_score": 0.95,
      "content_preview": "Deep learning is a subset..."
    }
  ],
  "citations": [
    {
      "document_title": "Deep Learning Guide",
      "document_uuid": "doc-uuid",
      "page_number": 10,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "search_results_count": 20,
    "reranked_results_count": 10,
    "total_sources": 3,
    "average_confidence": 0.87,
    "use_hybrid": true,
    "top_k": 10
  },
  "latency_ms": 245
}
```

**Example:**

```bash
curl -X POST "https://api.jarvis.ai/api/v1/knowledge/query" \
  -H "Authorization: Bearer <token>" \
  -F "query=Explain transformer architecture" \
  -F "top_k=5" \
  -F "max_tokens=2000"
```

---

### List Documents

List all documents for the authenticated user.

**Endpoint:** `GET /knowledge/documents`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | Number of documents to skip (default: 0) |
| limit | integer | No | Number of documents to return (default: 50) |
| status | string | No | Filter by status: `processing`, `indexed`, `failed`, `archived` |

**Response:** `200 OK`

```json
{
  "documents": [
    {
      "uuid": "doc-uuid-1",
      "title": "Machine Learning Guide",
      "file_name": "ml_guide.pdf",
      "document_type": "pdf",
      "status": "indexed",
      "chunk_count": 45,
      "token_count": 12500,
      "created_at": "2024-01-15T10:30:00Z",
      "indexed_at": "2024-01-15T10:35:00Z"
    }
  ],
  "count": 1
}
```

**Example:**

```bash
curl -X GET "https://api.jarvis.ai/api/v1/knowledge/documents?skip=0&limit=10&status=indexed" \
  -H "Authorization: Bearer <token>"
```

---

### Get Document Details

Get detailed information about a specific document.

**Endpoint:** `GET /knowledge/documents/{document_uuid}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_uuid | string | Yes | Document UUID |

**Response:** `200 OK`

```json
{
  "uuid": "doc-uuid",
  "title": "Machine Learning Guide",
  "file_name": "ml_guide.pdf",
  "document_type": "pdf",
  "status": "indexed",
  "chunk_count": 45,
  "token_count": 12500,
  "character_count": 75000,
  "language": "en",
  "metadata": {
    "author": "John Doe",
    "page_count": 30,
    "word_count": 15000
  },
  "chunking_strategy": "semantic",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "embedding_provider": "baai_bge",
  "created_at": "2024-01-15T10:30:00Z",
  "indexed_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses:**

- `404 Not Found`: Document not found

**Example:**

```bash
curl -X GET "https://api.jarvis.ai/api/v1/knowledge/documents/abc-123-def" \
  -H "Authorization: Bearer <token>"
```

---

### Delete Document

Delete a document from the knowledge base.

**Endpoint:** `DELETE /knowledge/documents/{document_uuid}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_uuid | string | Yes | Document UUID |

**Response:** `200 OK`

```json
{
  "message": "Document deleted successfully"
}
```

**Error Responses:**

- `404 Not Found`: Document not found

**Example:**

```bash
curl -X DELETE "https://api.jarvis.ai/api/v1/knowledge/documents/abc-123-def" \
  -H "Authorization: Bearer <token>"
```

---

### Get Knowledge Status

Get status and statistics for the user's knowledge base.

**Endpoint:** `GET /knowledge/status`

**Response:** `200 OK`

```json
{
  "document_count": 25,
  "chunk_count": 1250,
  "indexed_count": 20,
  "processing_count": 3,
  "failed_count": 2,
  "vector_store_stats": {
    "total_embeddings": 1250,
    "total_documents": 20,
    "dimension": 1024,
    "store_type": "pgvector"
  }
}
```

**Example:**

```bash
curl -X GET "https://api.jarvis.ai/api/v1/knowledge/status" \
  -H "Authorization: Bearer <token>"
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 413 | Payload Too Large - File size exceeds limit |
| 415 | Unsupported Media Type - Invalid file type |
| 500 | Internal Server Error - Server error |

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- Upload endpoint: 10 requests per minute
- Search endpoints: 60 requests per minute
- Query endpoints: 30 requests per minute
- Other endpoints: 100 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1640995200
```

## File Size Limits

Maximum file sizes by type:

- PDF: 50 MB
- DOCX: 50 MB
- PPTX: 50 MB
- Markdown: 10 MB
- Text: 10 MB
- HTML: 10 MB
- CSV: 50 MB
- JSON: 10 MB
- XML: 10 MB
- Images (OCR): 20 MB
- ZIP: 100 MB

## Supported File Types

| Type | Extensions | MIME Types |
|------|------------|------------|
| PDF | .pdf | application/pdf |
| DOCX | .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| PPTX | .pptx | application/vnd.openxmlformats-officedocument.presentationml.presentation |
| Markdown | .md | text/markdown, text/x-markdown |
| Text | .txt | text/plain |
| HTML | .html, .htm | text/html, application/xhtml+xml |
| CSV | .csv | text/csv, application/csv |
| JSON | .json | application/json |
| XML | .xml | application/xml, text/xml |
| Images | .png, .jpg, .jpeg, .tiff, .bmp | image/png, image/jpeg, image/tiff, image/bmp |
| ZIP | .zip | application/zip, application/x-zip-compressed |

## Chunking Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| semantic | Sentence boundary and topic segmentation | General documents, articles |
| recursive | Header-based hierarchical chunking | Structured documents, technical docs |
| sliding_window | Overlapping fixed-size windows | Code, logs, sequential data |
| parent_child | Large parent with small child chunks | Long documents needing context |
| adaptive | Content-aware dynamic sizing | Mixed content types |

## Embedding Providers

| Provider | Model | Dimension | Type |
|----------|-------|-----------|------|
| baai_bge | BAAI/bge-large-en-v1.5 | 1024 | Local |
| multilingual_e5 | intfloat/multilingual-e5-large | 1024 | Local |
| openai | text-embedding-3-small | 1536 | API |
| openai | text-embedding-3-large | 3072 | API |
| jina | jinaai/jina-embeddings-v2-base-en | 768 | Local |

## Best Practices

### Document Upload
1. Use appropriate chunking strategy for document type
2. Set chunk size based on content density
3. Use semantic chunking for general documents
4. Use recursive chunking for structured documents

### Search
1. Use specific queries for better results
2. Apply filters to narrow results
3. Use hybrid search for optimal quality
4. Adjust top_k based on use case

### RAG Query
1. Set appropriate max_tokens for context
2. Use citations for source attribution
3. Monitor latency for performance optimization
4. Use confidence scores for result filtering

### Error Handling
1. Implement retry logic for rate limits
2. Handle 404 errors gracefully
3. Log error responses for debugging
4. Monitor failed document processing

## SDK Examples

### Python

```python
import requests

API_BASE = "https://api.jarvis.ai/api/v1/knowledge"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Upload document
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{API_BASE}/upload",
        headers=headers,
        files={"file": f},
        data={
            "title": "My Document",
            "chunking_strategy": "semantic",
            "chunk_size": 1000
        }
    )
document_id = response.json()["document_id"]

# Index document
response = requests.post(
    f"{API_BASE}/index/{document_id}",
    headers=headers
)

# Search
response = requests.post(
    f"{API_BASE}/search",
    headers=headers,
    data={
        "query": "machine learning",
        "top_k": 10
    }
)
results = response.json()["results"]

# RAG query
response = requests.post(
    f"{API_BASE}/query",
    headers=headers,
    data={
        "query": "What is deep learning?",
        "top_k": 5,
        "max_tokens": 2000
    }
)
context = response.json()["context"]
```

### JavaScript

```javascript
const API_BASE = "https://api.jarvis.ai/api/v1/knowledge";
const TOKEN = "your-jwt-token";

const headers = {
  "Authorization": `Bearer ${TOKEN}`
};

// Upload document
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("title", "My Document");
formData.append("chunking_strategy", "semantic");

fetch(`${API_BASE}/upload`, {
  method: "POST",
  headers: headers,
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));

// Search
const searchParams = new URLSearchParams();
searchParams.append("query", "machine learning");
searchParams.append("top_k", "10");

fetch(`${API_BASE}/search`, {
  method: "POST",
  headers: headers,
  body: searchParams
})
  .then(response => response.json())
  .then(data => console.log(data.results));
```

## Changelog

### Version 1.0 (2024-01-15)
- Initial release
- Document upload and indexing
- Hybrid search
- RAG queries
- Document management
- Security features
