"""Liveness probe — thin HTTP adapter, no service dependencies."""

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}
