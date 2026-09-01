import requests
import json

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "epic015test@example.com", "password": "TestPassword123"}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== PHASE 4: Retrieval Test ===")
print()

# Test RAG query
query_data = {
    "query": "What is the exact identifier mentioned in the knowledge document?",
    "top_k": 5,
    "use_hybrid": True
}

rag_response = requests.post(
    "http://localhost:8000/api/v1/knowledge/query",
    data=query_data,
    headers=headers
)

result = rag_response.json()
print("RAG Query Response:")
print(json.dumps(result, indent=2))
print()

# Verify retrieval
print("=== Retrieval Verification ===")
print(f"Query: {result['query']}")
print(f"Answer: {result['answer']}")
print(f"Context length: {len(result['context']) if result['context'] else 0}")
print(f"Sources count: {len(result['sources'])}")
print(f"Citations count: {len(result['citations'])}")
print()

# Check if ORION-RAG-92841 is in context
if result['context'] and 'ORION-RAG-92841' in result['context']:
    print("✅ ORION-RAG-92841 found in retrieved context")
else:
    print("❌ ORION-RAG-92841 NOT found in retrieved context")

print()
print("=== PHASE 5: Real RAG Query ===")
print(f"Answer generated: {result['answer'] is not None}")
if result['answer']:
    print(f"Answer length: {len(result['answer'])}")
    if 'ORION-RAG-92841' in result['answer']:
        print("✅ Answer contains ORION-RAG-92841")
    else:
        print("❌ Answer does NOT contain ORION-RAG-92841")
