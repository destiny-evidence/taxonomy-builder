"""CLI entry point for running the MCP server over stdio."""

import asyncio

from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager


async def _run():
    db_manager.init(settings.effective_database_url)
    try:
        from taxonomy_builder.mcp.server import mcp

        await mcp.run_stdio_async()
    finally:
        await db_manager.close()


def main():
    asyncio.run(_run())
