import requests

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "epic015test@example.com", "password": "TestPassword123"}
)
token = login_response.json()["access_token"]
print("=== PHASE 2: Authentication ===")
print(f"Login: SUCCESS")
print(f"JWT obtained: {token[:50]}...")
print()

# Upload document
print("=== PHASE 3: Document Upload ===")
file_path = "epic015_test_document.txt"
with open(file_path, "rb") as f:
    files = {"file": ("epic015_test_document.txt", f, "text/plain")}
    data = {
        "title": "EPIC-015 RAG Test Document",
        "embedding_provider": "BAAI_BGE"
    }
    headers = {"Authorization": f"Bearer {token}"}
    upload_response = requests.post(
        "http://localhost:8000/api/v1/knowledge/upload",
        files=files,
        data=data,
        headers=headers
    )
    
print(f"Upload Response: {upload_response.json()}")
document_uuid = upload_response.json()["document_id"]
print(f"Document UUID: {document_uuid}")
print()

# Index document
print("=== Document Indexing ===")
index_response = requests.post(
    f"http://localhost:8000/api/v1/knowledge/index/{document_uuid}",
    headers=headers
)
print(f"Index Response: {index_response.json()}")
