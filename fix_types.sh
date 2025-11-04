#!/bin/bash
# Quick type fixing script for plex-mcp-server

echo "=== Type Fixing Helper Script ==="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "Step 1: Installing no_implicit_optional..."
uv pip install no_implicit_optional

echo ""
echo "Step 2: Running no_implicit_optional to fix implicit Optional parameters..."
no_implicit_optional src/plex_mcp_server

echo ""
echo "Step 3: Removing unused type: ignore comments..."
# Remove unused type: ignore comments from specific files
sed -i 's/ # type: ignore$//' src/plex_mcp_server/server.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/__main__.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/modules/user.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/modules/media.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/modules/library.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/modules/collection.py
sed -i 's/ # type: ignore$//' src/plex_mcp_server/modules/playlist.py

echo ""
echo "Step 4: Running ruff to format the changes..."
ruff format src/

echo ""
echo "Step 5: Checking remaining type errors..."
mypy src/plex_mcp_server 2>&1 | tail -20

echo ""
echo "=== Done! ==="
echo ""
echo "Next steps:"
echo "1. Review the TYPE_FIXING_GUIDE.md for detailed instructions"
echo "2. Fix remaining errors manually (see guide for patterns)"
echo "3. Run 'mypy src/plex_mcp_server' to check progress"
echo "4. Commit your changes when ready"
