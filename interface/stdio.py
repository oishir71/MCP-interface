from mcp.server import Server
from mcp.server.stdio import stdio_server


async def main(app: Server):
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())