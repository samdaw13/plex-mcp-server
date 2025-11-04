from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def sse_handler(scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI app for handling SSE connections and message posts."""
        path = scope.get("path", "/")

        # Handle SSE connection at /sse or /sse/
        if scope["type"] == "http" and scope["method"] == "GET" and path in ("/sse", "/sse/"):
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
        # Handle message posts at /messages/ (as configured in SseServerTransport)
        elif scope["type"] == "http" and path.startswith("/messages"):
            await sse.handle_post_message(scope, receive, send)
        else:
            # Return 404 for unknown paths
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
    )
