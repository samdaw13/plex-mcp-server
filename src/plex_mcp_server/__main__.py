"""Entry point for running the package as a module."""

import os

import uvicorn


def main() -> None:
    """Main entry point for the application."""
    host = os.environ.get("FASTMCP_HOST", "0.0.0.0")
    port = int(os.environ.get("FASTMCP_PORT", "3001"))
    debug = os.environ.get("FASTMCP_DEBUG", "False") == "True"
    reload = os.environ.get("FASTMCP_RELOAD", str(debug)).lower() in ("true", "1", "yes")

    print("Starting Plex MCP Server with SSE transport...")
    print(f"Server will listen on http://{host}:{port}")
    print("SSE endpoint: /sse")
    print(f"Plex URL: {os.environ.get('PLEX_URL', 'Not set')}")
    print(f"Debug mode: {debug}")
    print(f"Hot reload: {reload}")

    if reload:
        uvicorn.run(
            "plex_mcp_server.server:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=["src/plex_mcp_server"],
            timeout_graceful_shutdown=2,
        )
    else:
        uvicorn.run(
            "plex_mcp_server.server:app",
            host=host,
            port=port,
            timeout_graceful_shutdown=5,
        )


if __name__ == "__main__":
    main()
