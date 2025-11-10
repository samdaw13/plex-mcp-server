import os
from _asyncio import Task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .modules import mcp

active_connections: set[Task[None]] = set[Task[None]]()


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, Any]:
    """Handle application lifespan events."""
    yield None
    for task in list[Task[None]](active_connections):
        task.cancel()
    active_connections.clear()


async def list_tools_handler(request: Request) -> JSONResponse:
    """Handler for listing all available MCP tools."""
    tools_dict = await mcp.get_tools()
    tools_list = [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "output_schema": tool.output_schema,
            "annotations": tool.annotations.model_dump()
            if tool.annotations and hasattr(tool.annotations, "model_dump")
            else tool.annotations,
            "access": getattr(
                tool, "access", next(iter(tool.tags), "read") if tool.tags else "read"
            ),
        }
        for tool in tools_dict.values()
    ]

    return JSONResponse(tools_list)


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
            Route("/tools", endpoint=list_tools_handler, methods=["GET"]),
            Mount("/", app=sse_handler),
        ],
        lifespan=lifespan,
    )


debug = os.environ.get("FASTMCP_DEBUG", "False") == "True"
app = create_starlette_app(mcp._mcp_server, debug=debug)
