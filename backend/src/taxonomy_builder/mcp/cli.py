"""CLI entry point for running the MCP server over stdio."""

import asyncio

from taxonomy_builder.config import settings
from taxonomy_builder.database import db_manager
from taxonomy_builder.services.auth_service import AuthService


async def _run():
    db_manager.init(settings.effective_database_url)
    try:
        from taxonomy_builder.mcp import dependencies

        async with db_manager.session() as session:
            auth_service = AuthService(session)
            user = await auth_service.get_any_user()
            if user is None:
                raise SystemExit("No users in database. Log in via the UI first.")
            dependencies._stdio_user = user

        from taxonomy_builder.mcp.server import mcp

        await mcp.run_stdio_async()
    finally:
        await db_manager.close()


def main():
    asyncio.run(_run())
