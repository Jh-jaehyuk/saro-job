"""Tests for the ARQ smoke-test ping task."""


async def test_ping_returns_pong() -> None:
    from app.tasks.ping import ping

    result = await ping({})
    assert result == "pong"
