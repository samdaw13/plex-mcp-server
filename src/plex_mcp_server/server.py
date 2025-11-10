import os
import signal
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from .modules import mcp

active_connections: set = set()


@asynccontextmanager
async def lifespan(app: Starlette):
    """Handle application lifespan events."""
    yield
    for task in list(active_connections):
        task.cancel()
    active_connections.clear()


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def sse_handler(scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI app for handling SSE connections and message posts."""
        path = scope.get("path", "/")

        if scope["type"] == "http" and scope["method"] == "GET" and path in ("/sse", "/sse/"):
            try:
                async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                    import asyncio
                    task = asyncio.current_task()
                    if task:
                        active_connections.add(task)
                    try:
                        await mcp_server.run(
                            read_stream,
                            write_stream,
                            mcp_server.create_initialization_options(),
                        )
                    finally:
                        if task:
                            active_connections.discard(task)
            except Exception:
                pass
        elif scope["type"] == "http" and path.startswith("/messages"):
            await sse.handle_post_message(scope, receive, send)
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"Not Found",
                }
            )

    return Starlette(
        debug=debug,
        routes=[
            Mount("/", app=sse_handler),
        ],
        lifespan=lifespan,
    )


debug = os.environ.get("FASTMCP_DEBUG", "False") == "True"
app = create_starlette_app(mcp._mcp_server, debug=debug)
