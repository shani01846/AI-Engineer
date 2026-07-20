import asyncio
from contextlib import AsyncExitStack
from typing import Any
import os
import json
import httpx
from openai import OpenAI
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()


class ChatHost:
    def __init__(self):
        self.mcp_clients: list[MCPClient] = [MCPClient("./func.py")]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()
        # For Netfree

        # הגדרת ה-transport לנטפרי
        transport = httpx.HTTPTransport(verify=False)
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")

        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=gemini_api_key,
            http_client=httpx.Client(transport=transport),
        )

        # Try lightweight aliases/models first.
        preferred_model = (os.getenv("GEMINI_MODEL") or "").strip()
        self._models = [
            "gemini-flash-lite-latest",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.5-flash",
        ]
        if preferred_model:
            self._models = [preferred_model] + [m for m in self._models if m != preferred_model]
        print(f"Using Gemini model fallback order: {', '.join(self._models)}")

    @staticmethod
    def _is_quota_error(error: Exception) -> bool:
        error_text = str(error)
        return "429" in error_text or "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower()

    @staticmethod
    def _is_retryable_model_error(error: Exception) -> bool:
        error_text = str(error).lower()
        return "404" in error_text or "not found" in error_text or "unsupported" in error_text or "400" in error_text

    def _create_completion(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
        last_error: Exception | None = None
        for model_name in self._models:
            try:
                return self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                )
            except Exception as error:
                last_error = error
                if self._is_quota_error(error):
                    print(f"Model {model_name} quota exhausted, trying next Gemini model...")
                    continue
                if self._is_retryable_model_error(error):
                    print(f"Model {model_name} unavailable, trying next Gemini model...")
                    continue
                raise RuntimeError(f"Gemini call failed with model {model_name}: {error}") from error

        if last_error and self._is_quota_error(last_error):
            raise RuntimeError(
                "Gemini API quota is exhausted or unavailable for this project/key. "
                "Enable billing or use a key/project with active quota. "
                f"Last error: {last_error}"
            )

        raise RuntimeError(f"All configured Gemini models failed. Last error: {last_error}")

    async def connect_mcp_clients(self):
        """Connect all configured MCP clients once."""
        if self.clients_connected:
            return

        for client in self.mcp_clients:
            if client.session is None:
                await client.connect_to_server()

        if not self.mcp_clients:
            raise RuntimeError("No MCP clients are connected")

        self.clients_connected = True

    async def _call_tool_by_suffix(self, suffix: str, args: dict[str, Any] | None = None) -> str:
        args = args or {}
        for tool_name, (client, original_tool_name) in self.tool_clients.items():
            if tool_name.endswith(f"__{suffix}"):
                if client.session is None:
                    raise RuntimeError(f"MCP client {client.client_name} is not connected")
                result = await client.session.call_tool(original_tool_name, args)
                return str(result.content)
        raise RuntimeError(f"Tool not found: {suffix}")

    def _resolve_tool_name(self, requested_name: str) -> str:
        """Resolve model-requested tool names to actual registered MCP tool names."""
        if requested_name in self.tool_clients:
            return requested_name

        # Some models emit `client_tool` instead of `client__tool`.
        if "__" not in requested_name and "_" in requested_name:
            client_name, maybe_tool = requested_name.split("_", 1)
            candidate = f"{client_name}__{maybe_tool}"
            if candidate in self.tool_clients:
                return candidate

        # Last-resort suffix match.
        requested_suffix = requested_name.split("__")[-1]
        for registered_name in self.tool_clients:
            if registered_name.endswith(f"__{requested_suffix}"):
                return registered_name

        raise RuntimeError(f"Unknown tool requested by model: {requested_name}")

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Collect tools from all MCP clients and map them back to their owner."""
        await self.connect_mcp_clients()
        self.tool_clients = {}
        available_tools: list[dict[str, Any]] = []

        for client in self.mcp_clients:
            if client.session is None:
                print(f"Warning: MCP client {client.client_name} is not connected, skipping")
                continue

            try:
                response = await client.session.list_tools()
                for tool in response.tools:
                    exposed_name = f"{client.client_name}__{tool.name}"
                    if exposed_name in self.tool_clients:
                        raise RuntimeError(f"Duplicate tool name detected: {exposed_name}")

                    self.tool_clients[exposed_name] = (client, tool.name)
                    available_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": exposed_name,
                                "description": f"[{client.client_name}] {tool.description}",
                                "parameters": tool.inputSchema,
                            },
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to get tools from {client.client_name}: {str(e)}")
                continue

        if not available_tools:
            raise RuntimeError("No tools available from any MCP client")

        return available_tools


    async def process_query(self, query: str) -> str:
        """Process a query using Gemini chat completions and available MCP tools."""
        system_prompt = """
אתה סוכן תחזית מזג אוויר בישראל בלבד.

Workflow חובה:
1. קרא/open את אתר התחזית דרך open_weather_forecast_israel.
2. הזן את שם העיר דרך enter_weather_forecast_city_israel.
3. בחר את העיר דרך select_weather_forecast_city_israel.
4. חלץ תוכן דף דרך extract_weather_forecast_content_israel.
5. החזר תשובה תמציתית וברורה למשתמש על בסיס תוכן הדף בלבד.

כללים:
- אל תמציא מידע.
- אם לא הצלחת להשיג את התוכן, אמור מה נכשל ובאיזה שלב.
"""

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        available_tools = await self.get_available_tools()
        final_text = []

        try:
            while True:
                response = self._create_completion(messages=messages, tools=available_tools)

                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls or []
                saw_tool_use = len(tool_calls) > 0

                if assistant_message.content:
                    final_text.append(assistant_message.content)

                messages.append(assistant_message.model_dump(exclude_none=True))

                for tool_call in tool_calls:
                    tool_name = self._resolve_tool_name(tool_call.function.name)
                    raw_args = tool_call.function.arguments or "{}"
                    try:
                        tool_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                    client, original_tool_name = self.tool_clients[tool_name]
                    if client.session is None:
                        raise RuntimeError(f"MCP client {client.client_name} is not connected")

                    result = await client.session.call_tool(original_tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result.content),
                        }
                    )

                if not saw_tool_use:
                    break
        finally:
            try:
                await self._call_tool_by_suffix("close_browser")
            except Exception:
                pass

        return "\n".join(final_text)
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print("\n" + response)
                
            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")
                
    async def cleanup(self):
        """Clean up resources"""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()
        
        
async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()
        
if __name__ == "__main__":
    asyncio.run(main())