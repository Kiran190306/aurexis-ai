import requests
import os

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "epic015test@example.com", "password": "TestPassword123"}
)
token = login_response.json()["access_token"]

# Upload document
file_path = "test_e2e_document.txt"
with open(file_path, "rb") as f:
    files = {"file": ("test_e2e_document.txt", f, "text/plain")}
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
    
print("Upload Response:", upload_response.json())
document_uuid = upload_response.json()["document_id"]

# Index document
index_response = requests.post(
    f"http://localhost:8000/api/v1/knowledge/index/{document_uuid}",
    headers=headers
)
print("Index Response:", index_response.json())
