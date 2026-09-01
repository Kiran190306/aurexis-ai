import requests
import json

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "epic015test@example.com", "password": "TestPassword123"}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== PHASE 6: Negative Query Test ===")
print()

# Test negative query - question whose answer is NOT in the document
query_data = {
    "query": "What is the capital of France?",
    "top_k": 5,
    "use_hybrid": True
}

negative_response = requests.post(
    "http://localhost:8000/api/v1/knowledge/query",
    data=query_data,
    headers=headers
)

result = negative_response.json()
print("Negative Query Response:")
print(json.dumps(result, indent=2))
print()

# Verify no hallucination
print("=== Negative Query Verification ===")
print(f"Query: {result['query']}")
print(f"Answer: {result['answer']}")
print(f"Context length: {len(result['context']) if result['context'] else 0}")
print(f"Sources count: {len(result['sources'])}")

if result['answer'] is None:
    print("✅ No answer generated (correct - no hallucination)")
elif 'Paris' in result['answer'] or 'capital' in result['answer'].lower():
    print("❌ HALLUCINATION DETECTED - Answer contains information not in document")
else:
    print("⚠️ Answer generated but does not appear to hallucinate")

print()
print("=== PHASE 7: Citation Verification ===")
print(f"Citations count: {len(result['citations'])}")
for i, citation in enumerate(result['citations']):
    print(f"Citation {i+1}:")
    print(f"  Document Title: {citation['document_title']}")
    print(f"  Document UUID: {citation['document_uuid']}")
    print(f"  Confidence: {citation['confidence']}")
