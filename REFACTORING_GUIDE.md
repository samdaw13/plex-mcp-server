# MCP Tool Refactoring Guide

This guide documents the pattern for refactoring Plex MCP Server tools to use FastMCP 2 with proper Pydantic models, tags, and annotations.

## Table of Contents
1. [Overview](#overview)
2. [Complete Working Examples](#complete-working-examples)
3. [Step-by-Step Refactoring Process](#step-by-step-refactoring-process)
4. [Tag Assignment Rules](#tag-assignment-rules)
5. [Annotation Guidelines](#annotation-guidelines)
6. [Common Patterns](#common-patterns)
7. [Checklist](#checklist)

---

## Overview

### Goals
- **Strong typing**: Replace `json.dumps()` with Pydantic models
- **Proper tagging**: Add `tags={ToolTag.READ.value}` or `tags={ToolTag.WRITE.value}` or `tags={ToolTag.DELETE.value}`
- **Annotations**: Add `ToolAnnotations` with appropriate hints
- **Auto-generated schemas**: Let FastMCP generate input/output schemas from type annotations

### Key Changes
1. Import Pydantic models and `ToolAnnotations` from `mcp.types`
2. Update `@mcp.tool()` decorator with `tags` and `annotations`
3. Change return type from `-> str` to `-> SomeResponse | ErrorResponse`
4. Replace `json.dumps()` returns with Pydantic model instances

---

## Complete Working Examples

### Example 1: client_list (READ operation)

**BEFORE:**
```python
@mcp.tool()
async def client_list(include_details: bool = True) -> str:
    """List all available Plex clients connected to the server."""
    try:
        # ... logic ...
        return json.dumps({
            "status": "success",
            "message": f"Found {len(all_clients)} connected clients",
            "count": len(all_clients),
            "clients": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error: {str(e)}"})
```

**AFTER:**
```python
@mcp.tool(
    name="client_list",
    description="List all available Plex clients connected to the server",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def client_list(include_details: bool = True) -> ClientListResponse | ErrorResponse:
    """List all available Plex clients connected to the server."""
    try:
        # ... logic ...
        return ClientListResponse(
            status="success",
            message=f"Found {len(all_clients)} connected clients",
            count=len(all_clients),
            clients=result
        )
    except Exception as e:
        return ErrorResponse(message=f"Error: {str(e)}")
```

**Pydantic Models:**
```python
class ClientInfo(BaseModel):
    """Detailed information about a Plex client."""
    name: str
    device: str
    model: str
    # ... other fields ...

class ClientListResponse(BaseModel):
    """Response from client_list tool."""
    status: str
    message: str
    count: int
    clients: list[ClientInfo] | list[str]

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str
```

### Example 2: client_get_details (READ operation)

**BEFORE:**
```python
@mcp.tool()
async def client_get_details(client_name: str) -> str:
    """Get detailed information about a specific Plex client."""
    try:
        # ... logic ...
        client_details = {"name": client.title, "device": ...}
        return json.dumps({"status": "success", "client": client_details}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
```

**AFTER:**
```python
@mcp.tool(
    name="client_get_details",
    description="Get detailed information about a specific Plex client",
    tags={ToolTag.READ.value},
    annotations=ToolAnnotations(readOnlyHint=True)
)
async def client_get_details(client_name: str) -> ClientDetailsResponse | ErrorResponse:
    """Get detailed information about a specific Plex client."""
    try:
        # ... logic ...
        client_details = {"name": client.title, "device": ...}
        return ClientDetailsResponse(status="success", client=client_details)
    except Exception as e:
        return ErrorResponse(message=str(e))
```

---

## Step-by-Step Refactoring Process

### Step 1: Create Pydantic Response Models

Add models to `src/plex_mcp_server/types/models.py`:

```python
class YourToolResponse(BaseModel):
    """Response from your_tool."""
    status: str
    # Add all fields that your json.dumps returns
    message: str | None = None
    data: dict[str, Any] | None = None
```

**Tips:**
- Use `str | None` for optional fields
- Use `list[SomeModel]` for arrays of objects
- Use `dict[str, Any]` for flexible dictionaries
- Reuse `ErrorResponse` for all error cases

### Step 2: Update Imports

At the top of your module file:

```python
from mcp.types import ToolAnnotations
from . import connect_to_plex, mcp
from ..types.enums import ToolTag
from ..types.models import YourToolResponse, ErrorResponse
```

### Step 3: Update the Tool Decorator

```python
@mcp.tool(
    name="your_tool_name",  # Explicit name
    description="Clear description of what this tool does",  # From docstring first line
    tags={ToolTag.READ.value},  # or WRITE or DELETE
    annotations=ToolAnnotations(
        readOnlyHint=True,  # For READ operations
        # OR
        destructiveHint=True,  # For DELETE operations
        # OR
        idempotentHint=False  # For WRITE operations that aren't idempotent
    )
)
```

### Step 4: Update Function Signature

Change return type from `-> str` to `-> YourResponse | ErrorResponse`:

```python
async def your_tool_name(...) -> YourToolResponse | ErrorResponse:
```

### Step 5: Convert Return Statements

**Error returns:**
```python
# BEFORE
return json.dumps({"status": "error", "message": "Something failed"})

# AFTER
return ErrorResponse(message="Something failed")
```

**Success returns:**
```python
# BEFORE
return json.dumps({
    "status": "success",
    "message": "Operation completed",
    "data": some_data
}, indent=2)

# AFTER
return YourToolResponse(
    status="success",
    message="Operation completed",
    data=some_data
)
```

---

## Tag Assignment Rules

### READ Operations (`ToolTag.READ`)
**Use when:** Tool only reads/queries data, makes no changes
**Examples:**
- `client_list` - Lists clients
- `library_sections` - Lists library sections
- `media_search` - Searches for media

**Annotation:** `ToolAnnotations(readOnlyHint=True)`

### WRITE Operations (`ToolTag.WRITE`)
**Use when:** Tool creates, updates, or modifies data
**Examples:**
- `client_start_playback` - Starts playback
- `collection_create` - Creates a collection
- `playlist_add_items` - Adds items to playlist

**Annotation:** `ToolAnnotations(idempotentHint=False)` (most write operations)
**OR:** `ToolAnnotations(idempotentHint=True)` (if running twice has same effect as once)

### DELETE Operations (`ToolTag.DELETE`)
**Use when:** Tool permanently deletes data
**Examples:**
- `collection_delete` - Deletes a collection
- `playlist_delete` - Deletes a playlist

**Annotation:** `ToolAnnotations(destructiveHint=True, idempotentHint=True)`

---

## Annotation Guidelines

### ToolAnnotations Fields

```python
ToolAnnotations(
    title=None,  # Usually leave as None
    readOnlyHint=True,  # Set for READ operations
    destructiveHint=True,  # Set for DELETE operations
    idempotentHint=False,  # False if running twice has different effects
    openWorldHint=None  # Usually leave as None
)
```

### Common Patterns

**Safe read-only operations:**
```python
annotations=ToolAnnotations(readOnlyHint=True)
```

**Destructive operations:**
```python
annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True)
```

**Non-idempotent writes:**
```python
annotations=ToolAnnotations(idempotentHint=False)
```

**Idempotent writes:**
```python
annotations=ToolAnnotations(idempotentHint=True)
```

---

## Common Patterns

### Pattern 1: Simple List Response

```python
class ListItemResponse(BaseModel):
    status: str
    count: int
    items: list[dict[str, Any]]

# Usage
return ListItemResponse(
    status="success",
    count=len(items),
    items=items
)
```

### Pattern 2: Operation Success Response

```python
class OperationResponse(BaseModel):
    status: str
    message: str
    data: dict[str, Any] | None = None

# Usage
return OperationResponse(
    status="success",
    message="Operation completed successfully",
    data={"id": 123, "name": "example"}
)
```

### Pattern 3: Flexible Dict Response

For tools with complex/varying responses, use flexible types:

```python
class FlexibleResponse(BaseModel):
    status: str
    message: str | None = None
    # Allow any JSON-serializable data
    data: dict[str, str | int | float | bool | list | dict | None] | None = None
```

### Pattern 4: Nested Objects

```python
class MediaInfo(BaseModel):
    title: str
    year: int | None = None
    type: str

class SearchResponse(BaseModel):
    status: str
    count: int
    results: list[MediaInfo]  # Nested objects

# Usage
results = [MediaInfo(title=m.title, year=m.year, type=m.type) for m in media]
return SearchResponse(status="success", count=len(results), results=results)
```

---

## Checklist

When refactoring a tool, ensure you:

- [ ] Created Pydantic response model(s) in `types/models.py`
- [ ] Imported `ToolAnnotations` from `mcp.types`
- [ ] Imported your response models
- [ ] Imported `ToolTag` from `..types.enums`
- [ ] Added explicit `name` to decorator
- [ ] Added clear `description` to decorator
- [ ] Added appropriate `tags` (READ/WRITE/DELETE)
- [ ] Added appropriate `annotations`
- [ ] Updated function return type annotation
- [ ] Replaced ALL `json.dumps()` with Pydantic model instances
- [ ] Tested the tool works correctly
- [ ] Verified the tool schema in MCP server

---

## Testing Your Changes

After refactoring, rebuild and test:

```bash
# Rebuild docker image
docker compose build plex-mcp-sse

# Restart server
docker compose up -d plex-mcp-sse

# Check tool registration
docker compose exec plex-mcp-sse python << 'EOF'
from src.plex_mcp_server.modules import mcp
tool_manager = mcp._tool_manager
tool = tool_manager._tools['your_tool_name']
print(f"Name: {tool.name}")
print(f"Tags: {tool.tags}")
print(f"Annotations: {tool.annotations}")
EOF
```

---

## Next Steps

1. Start with READ operations (simplest)
2. Then WRITE operations
3. Finally DELETE operations
4. Test each module after refactoring
5. Create PR when complete

## Reference Files

- **Complete example:** `src/plex_mcp_server/modules/client.py` (client_list, client_get_details)
- **Models:** `src/plex_mcp_server/types/models.py`
- **Enums:** `src/plex_mcp_server/types/enums.py`
