"""
Tests for health endpoint.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(test_config):
    """GET /health returns 200 with status ok."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"
    assert "vector_store_size" in data
    assert "embedding_model" in data
    assert "llm_provider" in data
    assert "mock_mode" in data


@pytest.mark.asyncio
async def test_health_mock_mode_flag(test_config):
    """Health endpoint correctly reports mock_mode."""
    cfg = test_config
    cfg_mock = cfg  # re-use, already mock_mode=True
    from main import create_app

    app = create_app(cfg_mock)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["mock_mode"] is True


@pytest.mark.asyncio
async def test_health_response_model(test_config):
    """Health response matches HealthResponse schema."""
    from main import create_app
    from models.schemas import HealthResponse

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    # Verify it can be parsed as HealthResponse
    health = HealthResponse(**response.json())
    assert health.status == "ok"
    assert health.version == "0.2.0"
