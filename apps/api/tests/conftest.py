"""Shared pytest fixtures for apps/api tests."""

from collections.abc import Iterator

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a synchronous TestClient bound to the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client
