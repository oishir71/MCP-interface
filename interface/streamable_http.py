import uvicorn
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send


async def main(app: Server, host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
    session_manager = StreamableHTTPSessionManager(app=app)

    async def health_check(request) -> PlainTextResponse:
        return PlainTextResponse("Healthy")

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    routes: list[Route | Mount] = []
    routes.append(Route("/health_check", endpoint=health_check, methods=["GET"]))
    # MCP server uses /mcp endpoint by default,
    # however, it seems / is used in some cases.
    routes.append(Mount("/", app=handle_streamable_http))
    routes.append(Mount("/mcp", app=handle_streamable_http))

    # TODO: check what middleware and lifespan is.
    starlette_app = Starlette(debug=False, routes=routes, middlewares=[], lifespan=lambda app: session_manager.run())

    config = uvicorn.Config(starlette_app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    await server.serve()