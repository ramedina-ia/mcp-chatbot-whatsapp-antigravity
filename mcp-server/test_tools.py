import sys
import os

os.environ["EVOLUTION_API_URL"] = "https://mock-evolution.local"
os.environ["EVOLUTION_API_KEY"] = "mock-key"
os.environ["TYPEBOT_VIEWER_URL"] = "https://mock-bot.local"
os.environ["CHATWOOT_API_URL"] = "https://mock-chat.local"

from server import mcp

async def test_tools():
    tools = await mcp.list_tools()
    print(f"Total herramientas registradas en FastMCP: {len(tools)}")
    for t in tools:
        print(f" - Tool: {t.name} -> {t.description[:60]}...")
    print("\n¡Prueba de servidor FastMCP completada con éxito!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools())
