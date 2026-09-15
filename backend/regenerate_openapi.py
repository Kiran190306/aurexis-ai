import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
import json

# Generate new OpenAPI schema
openapi_schema = app.openapi()

# Save to both locations
with open('openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI schema regenerated successfully")
print(f"Model defaults should now show: gpt-4o-mini")
