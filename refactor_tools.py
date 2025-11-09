#!/usr/bin/env python3
"""Helper script to batch-convert remaining client tools to Pydantic pattern."""

import re

# Read the client.py file
with open('src/plex_mcp_server/modules/client.py', 'r') as f:
    content = f.read()

# Pattern replacements for common json.dumps patterns
replacements = [
    # Simple error responses
    (
        r'return json\.dumps\(\{"status": "error", "message": f"([^"]+)"\}\)',
        r'return ErrorResponse(message=f"\1")'
    ),
    (
        r'return json\.dumps\(\{"status": "error", "message": "([^"]+)"\}\)',
        r'return ErrorResponse(message="\1")'
    ),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Write back
with open('src/plex_mcp_server/modules/client.py', 'w') as f:
    f.write(content)

print("✓ Converted simple error responses")
print("Note: Complex responses need manual conversion to appropriate Pydantic models")
