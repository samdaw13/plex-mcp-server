# Plex MCP Server

A Model Context Protocol (MCP) server for Plex Media Server, providing a standardized interface for AI assistants, automation tools, and custom integrations to interact with your Plex server.

## Overview

Plex MCP Server creates a unified MCP-compliant API layer on top of the Plex Media Server API, offering:

- **MCP Protocol Compliance** - Works seamlessly with Claude Desktop, Cline, and other MCP clients
- **Standardized JSON responses** for compatibility with automation tools, AI systems, and other integrations
- **Multiple transport methods** (stdio and SSE) for flexible integration options
- **Rich tool set** - 60+ tools for managing libraries, collections, playlists, media, users, playback, and more
- **Error handling** with consistent response formats
- **Docker support** for easy deployment
- **Connection pooling** with automatic reconnection for reliability

## Requirements

- Python 3.13+
- Plex Media Server with valid authentication token
- Access to the Plex server (locally or remotely)

## Installation

### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone this repository
git clone https://github.com/yourusername/plex-mcp-server.git
cd plex-mcp-server

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env with your Plex server details
```

### Option 2: Using pip

```bash
# Clone this repository
git clone https://github.com/yourusername/plex-mcp-server.git
cd plex-mcp-server

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Plex server details
```

### Option 3: Using Docker

```bash
# Clone this repository
git clone https://github.com/yourusername/plex-mcp-server.git
cd plex-mcp-server

# Create .env file
cp .env.example .env
# Edit .env with your Plex server details

# Start the server with Docker Compose
docker-compose up -d
```

### Environment Variables

Configure your `.env` file with the following variables:

```bash
# Plex Configuration
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your-plex-token
PLEX_USERNAME=your-username  # Optional, used for some user-specific queries

# FastMCP Server Configuration (for SSE mode)
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=3001
```

**Finding Your Plex Token:**
See [Plex's official guide](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) for instructions on obtaining your authentication token.

## Usage

The server can be run in two transport modes: stdio (Standard Input/Output) or SSE (Server-Sent Events). Each mode is suitable for different integration scenarios.

### Running with stdio Transport

The stdio transport is ideal for direct integration with MCP clients like Claude Desktop, Cline, or other AI assistants.

#### Using Python Module (Recommended)
```bash
python -m plex_mcp_server
```

#### Using Legacy Script (Still supported)
```bash
python plex_mcp_server.py --transport stdio
```

#### Configuration for Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "plex": {
      "command": "python",
      "args": [
        "-m",
        "plex_mcp_server"
      ],
      "env": {
        "PLEX_URL": "http://localhost:32400",
        "PLEX_TOKEN": "your-plex-token",
        "PLEX_USERNAME": "your-username"
      }
    }
  }
}
```

**Note:** If using uv, you can also use:
```json
{
  "mcpServers": {
    "plex": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/plex-mcp-server",
        "run",
        "plex-mcp-server"
      ],
      "env": {
        "PLEX_URL": "http://localhost:32400",
        "PLEX_TOKEN": "your-plex-token",
        "PLEX_USERNAME": "your-username"
      }
    }
  }
}
```

### Running with SSE Transport

The Server-Sent Events (SSE) transport provides a web-based interface for integration with web applications, automation platforms, and remote MCP clients.

#### Using Python Module (Default)
```bash
python -m plex_mcp_server
```
This starts the SSE server on `http://0.0.0.0:3001` by default.

#### Using Legacy Script with Custom Options
```bash
python plex_mcp_server.py --transport sse --host 0.0.0.0 --port 3001
```

#### Using Docker
```bash
docker-compose up -d
```

The server will be available at:
- SSE endpoint: `http://localhost:3001/sse`
- Message endpoint: `http://localhost:3001/messages/`

#### Configuration for MCP Clients (SSE Mode)

```json
{
  "mcpServers": {
    "plex": {
      "url": "http://localhost:3001/sse"
    }
  }
}
```

## Available Tools (60+ MCP Tools)

The server exposes all functionality as MCP tools that can be called by any MCP client. Here's an overview organized by module:

### Library Module (7 tools)
- `library_list` - List all libraries on the server
- `library_get_stats` - Get statistics for a specific library
- `library_refresh` - Refresh a library or all libraries
- `library_scan` - Scan a library for new content
- `library_get_details` - Get detailed information about a library
- `library_get_recently_added` - Get recently added media
- `library_get_contents` - Get full contents of a library

### Media Module (7 tools)
- `media_search` - Search for media across all libraries
- `media_get_details` - Get detailed information about a specific media item
- `media_edit_metadata` - Edit metadata for media items
- `media_delete` - Delete media from the library
- `media_get_artwork` - Get artwork/images for media
- `media_set_artwork` - Set custom artwork for media
- `media_list_available_artwork` - List all available artwork options

### Playlist Module (9 tools)
- `playlist_list` - List all playlists
- `playlist_get_contents` - Get contents of a specific playlist
- `playlist_create` - Create a new playlist
- `playlist_delete` - Delete a playlist
- `playlist_add_to` - Add items to a playlist
- `playlist_remove_from` - Remove items from a playlist
- `playlist_edit` - Edit playlist details (title, summary)
- `playlist_upload_poster` - Upload custom poster for a playlist
- `playlist_copy_to_user` - Copy a playlist to another user's account

### Collection Module (6 tools)
- `collection_list` - List all collections
- `collection_create` - Create a new collection
- `collection_add_to` - Add items to a collection
- `collection_remove_from` - Remove items from a collection
- `collection_delete` - Delete a collection
- `collection_edit` - Comprehensively edit collection attributes (title, summary, artwork, labels, advanced settings)

### User Module (5 tools)
- `user_search_users` - Search for users or list all users
- `user_get_info` - Get detailed information about a user
- `user_get_on_deck` - Get on deck (in progress) media for a user
- `user_get_watch_history` - Get recent watch history for a user
- `user_get_statistics` - Get watch statistics for users over different time periods

### Sessions Module (2 tools)
- `sessions_get_active` - Get current playback sessions with IP addresses
- `sessions_get_media_playback_history` - Get playback history for a specific media item

### Server Module (7 tools)
- `server_get_plex_logs` - Get Plex server logs
- `server_get_info` - Get detailed server information
- `server_get_bandwidth` - Get bandwidth statistics
- `server_get_current_resources` - Get resource usage information
- `server_get_butler_tasks` - Get information about scheduled butler tasks
- `server_run_butler_task` - Manually run a specific butler task
- `server_get_alerts` - Get real-time server alerts via websocket

### Client Module (8 tools)
- `client_list` - List all available Plex clients
- `client_get_details` - Get detailed information about a client
- `client_get_timelines` - Get current timeline information for a client
- `client_get_active` - Get all clients currently playing media
- `client_start_playback` - Start playback of media on a client
- `client_control_playback` - Control playback (play, pause, stop, seek, volume)
- `client_navigate` - Navigate a client interface (up, down, select, back, home)
- `client_set_streams` - Set audio, subtitle, or video streams

**Note:** Client module functionality depends on having active Plex clients connected to your server. Some features may have limitations depending on the client type and capabilities.

## Response Format

All commands return standardized JSON responses for maximum compatibility with various tools, automation platforms, and AI systems. This consistent structure makes it easy to process responses programmatically.

For successful operations, the response typically includes:
```json
{
  "success_field": true,
  "relevant_data": "value",
  "additional_info": {}
}
```

For errors, the response format is:
```json
{
  "error": "Error message describing what went wrong"
}
```

For multiple matches (when searching by title), results are returned as an array of objects with identifying information:
```json
[
  {
    "title": "Item Title",
    "id": 12345,
    "type": "movie",
    "year": 2023
  },
  {
    "title": "Another Item",
    "id": 67890,
    "type": "show",
    "year": 2022
  }
]
```

## Development & Debugging

### Using the Watcher Script

For development and debugging, you can use the included `watcher.py` script which monitors for file changes and automatically restarts the server:

```bash
python watcher.py
```

This is useful during development to see changes immediately without manually restarting the server.

### Running Tests

If you have pytest installed (included in dev dependencies):

```bash
# Install dev dependencies with uv
uv sync --group dev

# Or with pip
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Debug Mode

Enable debug mode for more verbose logging:

```bash
python plex_mcp_server.py --transport sse --debug
```

## Architecture

The server is built using:
- **FastMCP** - A high-performance MCP server framework
- **PlexAPI** - Official Python bindings for the Plex API
- **Starlette/Uvicorn** - ASGI web framework for SSE transport
- **Python 3.13+** - Latest Python features and performance

### Project Structure

```
plex-mcp-server/
├── src/plex_mcp_server/
│   ├── __init__.py
│   ├── __main__.py          # Main entry point
│   ├── server.py            # Server setup and routing
│   └── modules/
│       ├── __init__.py      # MCP instance and connection management
│       ├── library.py       # Library tools
│       ├── media.py         # Media tools
│       ├── playlist.py      # Playlist tools
│       ├── collection.py    # Collection tools
│       ├── user.py          # User tools
│       ├── sessions.py      # Session tools
│       ├── server.py        # Server tools
│       └── client.py        # Client tools
├── plex_mcp_server.py      # Legacy entry point
├── docker-compose.yml       # Docker setup
├── Dockerfile              # Container definition
├── pyproject.toml          # Project metadata and dependencies
├── requirements.txt        # Pip requirements
└── README.md              # This file
```

## Use Cases

- **AI Assistant Integration** - Let Claude or other AI assistants manage your Plex library
- **Home Automation** - Integrate with Home Assistant, n8n, or other automation platforms
- **Custom Dashboards** - Build custom monitoring and control interfaces
- **Batch Operations** - Automate bulk metadata updates, organization, and cleanup
- **Content Management** - Programmatically manage collections, playlists, and media
- **Analytics** - Track viewing habits and generate custom reports
- **Remote Control** - Control playback on Plex clients from anywhere

## Troubleshooting

### Connection Issues

If you're having trouble connecting to your Plex server:

1. Verify your `PLEX_URL` is correct and accessible
2. Ensure your `PLEX_TOKEN` is valid (tokens can expire)
3. Check network connectivity between the MCP server and Plex server
4. Review logs for specific error messages

### MCP Client Integration

If your MCP client can't see the server:

1. For stdio mode: Ensure the command path is correct in your client config
2. For SSE mode: Verify the server is running and accessible at the configured URL
3. Check environment variables are properly set
4. Restart your MCP client after configuration changes

### Common Errors

- **"Failed to connect to Plex"** - Check PLEX_URL and PLEX_TOKEN
- **"Library not found"** - Verify the library name exactly matches what's in Plex
- **"Module not found"** - Ensure dependencies are installed (`uv sync` or `pip install -r requirements.txt`)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) by @jlowin
- Uses [PlexAPI](https://github.com/pkkid/python-plexapi) for Plex integration
- Follows the [Model Context Protocol](https://modelcontextprotocol.io/) specification
