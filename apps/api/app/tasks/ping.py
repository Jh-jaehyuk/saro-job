"""Smoke-test task for the ARQ worker."""


async def ping(ctx: dict[str, object]) -> str:
    """Smoke-test task for the ARQ worker."""
    return "pong"
