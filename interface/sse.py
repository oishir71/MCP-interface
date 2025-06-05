import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send


async def main(app: Server, host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
    sse = SseServerTransport("/messages/")

    async def health_check(request: Request) -> PlainTextResponse:
        return PlainTextResponse("Healthy")

    async def handle_sse(scope: Scope, receive: Receive, send: Send):
        async with sse.connect_sse(scope, receive, send) as stream:
            await app.run(stream[0], stream[1], app.create_initialization_options())
        return Response()

    async def sse_endpoint(request: Request) -> Response:
        return await handle_sse(request.scope, request.receive, request._send)

    routes: list[Route | Mount] = []
    routes.append(Route("/health_check", endpoint=health_check, methods=["GET"]))
    # MCP server uses /sse endpoint by default,
    # however, it seems / is used in some cases.
    routes.append(Route("/", endpoint=sse_endpoint, methods=["GET"]))
    routes.append(Route("/sse", endpoint=sse_endpoint, methods=["GET"]))
    routes.append(Mount("/messages/", app=sse.handle_post_message))

    # TODO: check what middleware is.
    starlette_app = Starlette(debug=False, routes=routes, middlewares=[])

    config = uvicorn.Config(starlette_app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    await server.serve()