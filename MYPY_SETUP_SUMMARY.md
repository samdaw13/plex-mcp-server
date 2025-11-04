# MyPy Setup Summary

## ✅ What's Been Configured

### 1. **MyPy Installed and Configured**
   - Added mypy 1.18.2 to dev dependencies
   - Added types-requests for type stubs
   - Configured in `pyproject.toml` with strict mode enabled

### 2. **Pre-commit Hook Setup**
   - Pre-commit hooks installed at `.git/hooks/pre-commit`
   - Will run on every commit:
     1. **Ruff linter** - Auto-fixes code issues
     2. **Ruff formatter** - Formats code
     3. **MyPy** - Type checks staged Python files

### 3. **Configuration Details**

   **MyPy Configuration** (`pyproject.toml`):
   - ✅ Strict mode enabled
   - ✅ No implicit Optional
   - ✅ Disallow untyped definitions
   - ✅ Python 3.13 target
   - ✅ Ignoring missing imports for third-party libraries (plexapi, mcp, dotenv)

   **Pre-commit Configuration** (`.pre-commit-config.yaml`):
   - ✅ Runs only on staged files (fast!)
   - ✅ Only checks Python files in src/

## 📊 Current Status

**Type Errors Found:** 232 errors across 11 files

**Error Breakdown:**
- 🔴 114 errors: Implicit Optional (missing `| None` in type hints)
- 🟡  22 errors: Unreachable code
- 🟡  22 errors: String type issues
- 🔴  21 errors: Calls to untyped functions
- 🟡  13 errors: Missing variable type annotations
- 🟡  13 errors: Union attribute access
- 🟢  11 errors: Unused `# type: ignore` comments
- 🔴   9 errors: Functions missing type annotations

## 🚀 Quick Start - Fix Types Now

### Option 1: Automated Quick Fixes (Recommended)

Run the helper script:
```bash
./fix_types.sh
```

This will:
1. Install `no_implicit_optional` tool
2. Auto-fix implicit Optional parameters (~114 errors)
3. Remove unused `# type: ignore` comments (~11 errors)
4. Format the code with ruff
5. Show remaining errors

**Expected result:** ~125 errors fixed automatically, ~107 remaining

### Option 2: Manual Step-by-Step

Follow the detailed guide:
```bash
cat TYPE_FIXING_GUIDE.md
```

### Option 3: Gradual Approach

1. **Start with one file:**
   ```bash
   mypy src/plex_mcp_server/modules/__init__.py
   ```

2. **Fix errors in that file** using the guide

3. **Move to next file** and repeat

## 📝 Common Fix Patterns

### Fix #1: Implicit Optional (Most Common)
**Before:**
```python
async def my_function(param: str = None) -> str:
    pass
```

**After:**
```python
async def my_function(param: str | None = None) -> str:
    pass
```

### Fix #2: Missing Return Type
**Before:**
```python
def helper_function():
    return {"key": "value"}
```

**After:**
```python
def helper_function() -> dict[str, Any]:
    return {"key": "value"}
```

### Fix #3: Float vs Int
**Before:**
```python
last_connection_time: int = 0
last_connection_time = time.time()  # Error: float assigned to int
```

**After:**
```python
last_connection_time: float = 0.0
last_connection_time = time.time()  # OK
```

## 🧪 Testing Your Changes

After fixing errors:

```bash
# Check type errors
mypy src/plex_mcp_server

# Run linter
ruff check .

# Run tests
pytest

# Test pre-commit hook
pre-commit run --all-files
```

## 🛡️ Pre-commit Hook Behavior

When you commit code:

1. **Ruff** will automatically fix and format your code
2. **MyPy** will check types on your staged files
3. **If mypy finds errors:** Commit will be rejected
4. **Fix the errors** and commit again

To bypass (not recommended):
```bash
git commit --no-verify -m "WIP"
```

## 📚 Resources Created

1. **TYPE_FIXING_GUIDE.md** - Comprehensive guide with examples
2. **fix_types.sh** - Automated fixing script
3. **MYPY_SETUP_SUMMARY.md** - This file

## 🎯 Next Steps

### Immediate (Do Now):
1. Run `./fix_types.sh` to fix ~125 errors automatically
2. Review the changes with `git diff`
3. Commit the auto-fixes: `git add . && git commit -m "fix: auto-fix type hints with no_implicit_optional"`

### Short-term (This Week):
1. Read `TYPE_FIXING_GUIDE.md` 
2. Fix remaining ~107 errors file by file
3. Each time you fix a file, commit it

### Long-term (Ongoing):
1. Write new code with proper type hints from the start
2. Pre-commit hook will catch type errors before commit
3. Gradually improve type coverage

## 💡 Tips

- **Start small:** Fix one file at a time
- **Run mypy often:** `mypy <file>` to check progress
- **Use IDE hints:** VS Code and PyCharm show mypy errors inline
- **Ask for help:** Check the error code in mypy docs

## 🔧 Adjusting Strictness

If strict mode is too aggressive, you can temporarily relax it in `pyproject.toml`:

```toml
[tool.mypy]
# Change from:
strict = true

# To:
strict = false
check_untyped_defs = true
disallow_untyped_defs = true
no_implicit_optional = true
```

Then gradually re-enable strict mode as you fix errors.

## ✅ Success Criteria

You'll know you're done when:
```bash
$ mypy src/plex_mcp_server
Success: no issues found in 13 source files
```

Good luck! 🚀
