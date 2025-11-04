# Type Fixing Guide for plex-mcp-server

This guide will help you systematically fix the 232 type errors detected by mypy.

## Error Summary

- **[assignment]** (114): Implicit Optional parameters - Functions with `= None` defaults need proper type hints
- **[unreachable]** (22): Unreachable code detected
- **[no-untyped-call]** (21): Calls to functions without type annotations
- **[var-annotated]** (13): Variables missing type annotations
- **[union-attr]** (13): Attribute access on Union types needs proper handling
- **[unused-ignore]** (11): Unused `# type: ignore` comments
- **[no-untyped-def]** (9): Functions missing type annotations

## Quick Fixes

### 1. Fix Implicit Optional Parameters (Most Common)

**Problem:**
```python
async def my_function(param: str = None) -> str:
    pass
```

**Solution:**
```python
async def my_function(param: str | None = None) -> str:
    pass
```

**Auto-fix script:**
```bash
# Install no_implicit_optional
pip install no_implicit_optional

# Run the fixer
no_implicit_optional src/plex_mcp_server
```

### 2. Remove Unused `# type: ignore` Comments

**Problem:**
```python
from mcp.server import Server  # type: ignore
```

**Solution:**
```python
# Since mypy now ignores this in the config, just remove the comment
from mcp.server import Server
```

**Manual fix:** Search for `# type: ignore` and remove where mypy says unused.

### 3. Add Missing Return Type Annotations

**Problem:**
```python
def my_function():
    return "result"
```

**Solution:**
```python
def my_function() -> str:
    return "result"
```

### 4. Fix float vs int Type Issues

**Problem:**
```python
last_connection_time: int = 0
# Later...
last_connection_time = time.time()  # time.time() returns float!
```

**Solution:**
```python
last_connection_time: float = 0.0
# Or if you need int:
last_connection_time = int(time.time())
```

### 5. Add Type Annotations for Variables

**Problem:**
```python
filtered_items = []  # mypy doesn't know what type of items
```

**Solution:**
```python
from typing import Any
filtered_items: list[Any] = []
# Or better, if you know the type:
filtered_items: list[dict[str, Any]] = []
```

### 6. Handle Union Types Safely

**Problem:**
```python
def process(value: str | None):
    return value.lower()  # Error: value might be None!
```

**Solution:**
```python
def process(value: str | None) -> str:
    if value is None:
        return ""
    return value.lower()
```

## Step-by-Step Fixing Process

### Phase 1: Auto-fixable Issues

1. **Install and run no_implicit_optional:**
   ```bash
   uv pip install no_implicit_optional
   no_implicit_optional src/plex_mcp_server
   ```

2. **Remove unused type: ignore comments:**
   ```bash
   # Manually go through each file and remove unused comments
   # Files affected: server.py, __main__.py, user.py, media.py, library.py, collection.py, playlist.py
   ```

### Phase 2: Type Annotations

3. **Add return type annotations to all functions:**
   - Start with `__init__.py` and `__main__.py`
   - Move through each module file
   - For MCP tool functions: they all return `str` (JSON strings)
   - For helper functions: determine the actual return type

4. **Fix variable type annotations:**
   ```bash
   mypy src/plex_mcp_server 2>&1 | grep "var-annotated"
   ```
   Add type hints for each variable listed.

5. **Fix unreachable code:**
   ```bash
   mypy src/plex_mcp_server 2>&1 | grep "unreachable"
   ```
   Review each unreachable code warning and fix the logic or remove the code.

### Phase 3: Complex Fixes

6. **Fix Union attribute access:**
   Add proper None checks before accessing attributes.

7. **Add type hints to untyped function calls:**
   Add return types to helper functions that are called from typed contexts.

## Testing Your Changes

After fixing a batch of errors:

```bash
# Run mypy to check progress
mypy src/plex_mcp_server

# Run ruff to ensure code quality
ruff check .

# Run tests
pytest

# Try the pre-commit hook
pre-commit run --all-files
```

## Common Patterns in This Codebase

### MCP Tool Functions
All functions decorated with `@mcp.tool()` should follow this pattern:

```python
@mcp.tool()
async def tool_name(
    param1: str,
    param2: int | None = None,
    param3: str | None = None,
) -> str:
    """Tool description.

    Args:
        param1: Description
        param2: Optional description
        param3: Optional description
    """
    try:
        # Implementation
        return json.dumps({"status": "success", "data": result})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
```

### Helper Functions
```python
def helper_function(param: str) -> dict[str, Any]:
    """Helper description."""
    return {"key": "value"}
```

### Connection Functions
```python
def connect_to_plex() -> PlexServer:
    """Connection description."""
    global server, last_connection_time
    # Implementation
    return server
```

## Gradual Typing Approach

If 232 errors feel overwhelming, you can:

1. **Disable strict mode temporarily** in `pyproject.toml`:
   ```toml
   [tool.mypy]
   strict = false  # Change to false
   # Keep these enabled:
   check_untyped_defs = true
   disallow_untyped_defs = true
   no_implicit_optional = true
   ```

2. **Fix errors file by file:**
   ```bash
   # Check one file at a time
   mypy src/plex_mcp_server/modules/__init__.py
   ```

3. **Gradually enable stricter checks** as you fix errors.

## Pre-commit Hook Behavior

The pre-commit hook will now:
1. Run ruff linter with auto-fix
2. Run ruff formatter
3. Run mypy type checker (will fail commit if errors found)

To bypass temporarily (not recommended):
```bash
git commit --no-verify -m "WIP: fixing types"
```

## Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [no_implicit_optional](https://github.com/hauntsaninja/no_implicit_optional)

## Get Help

If you encounter specific errors you're unsure how to fix:
```bash
# Get detailed error explanation
mypy src/plex_mcp_server --show-error-codes --pretty

# Check specific file with verbose output
mypy src/plex_mcp_server/modules/client.py --verbose
```
