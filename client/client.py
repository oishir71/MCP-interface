import asyncio
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import EmbeddedResource, ImageContent, TextContent


class MCPClient:
    def __init__(self, server_parameters: dict[str, Any]):
        self.server_parameters = server_parameters
        self.session: Optional[ClientSession] = None

        self.exit_stack = AsyncExitStack()

    async def _connect_stdio_server(self):
        if ("command" not in self.server_parameters or
                "args" not in self.server_parameters):
            raise ValueError("Server parameters must include 'command' and 'args'")

        server_params = StdioServerParameters(
            command=self.server_parameters.get("command"),
            args=self.server_parameters.get("args"),
            env=self.server_parameters.get("env", None),
        )
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()
        return self

    async def _connect_sse_server(self):
        if "url" not in self.server_parameters:
            raise ValueError("Server parameters must include 'url'")

        url = self.server_parameters.get("url")
        sse_transport = await self.exit_stack.enter_async_context(sse_client(url=url))
        self.stdio, self.write = sse_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()
        return self

    async def _connect_streamablehttp_server(self):
        if "url" not in self.server_parameters:
            raise ValueError("Server parameters must include 'url'")

        url = self.server_parameters.get("url")
        streamablehttp_transport = await self.exit_stack.enter_async_context(
            streamablehttp_client(url=url)
        )
        self.stdio, self.write, _ = streamablehttp_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()
        return self


    async def __aenter__(self):
        transport = self.server_parameters.get("transport", "stdio")
        if transport == "stdio":
            return await self._connect_stdio_server()
        elif transport == "sse":
            return await self._connect_sse_server()
        elif transport == "streamable_http":
            return await self._connect_streamablehttp_server()
        else:
            raise ValueError(f"Unknown transport type: {transport}")

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def _get_tools(self):
        list_tools_response = await self.session.list_tools()
        # TODO: OpenAI tool format is only taken into account
        # Might be better to support Bedrock case.
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in list_tools_response.tools
        ]

    def _encode_tool_content(self, content: TextContent | ImageContent | EmbeddedResource) -> dict[str, Any]:
        if isinstance(content, TextContent):
            return {"type": "text", "text": content.text}
        elif isinstance(content, ImageContent):
            return {"type": "image_url", "image_url": {"url": content.url}}
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

    async def execute_tool(self, name: str, arguments: dict[str, Any]):
        result = await self.session.call_tool(name, arguments)
        return [self._encode_tool_content(c) for c in result.content]

async def main(server_parameters: dict[str, Any]):
    async with MCPClient(server_parameters) as client:
        await client.execute_tool(name="get_softreef_component_file_path", arguments={"component": "TextBox"})

if __name__ == "__main__":
    server_parameters = {
        "transport": "streamable_http",
        "url": "http://localhost:9999",
    }
    asyncio.run(main(server_parameters))