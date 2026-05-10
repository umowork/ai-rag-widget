"""
Tests for chat endpoints (sync + stream).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_chat_post_returns_answer(test_config):
    """POST /chat with valid query returns answer and sources."""
    from main import create_app

    # Need to seed some docs first
    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First upload some text
        await client.post(
            "/upload/text",
            data={"text": "Компания основана в 2010 году.", "source": "about"},
        )

        # Then query
        response = await client.post("/chat", json={"query": "Когда основана компания?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "model_used" in data
    assert "mock-llm" in data["model_used"]
    assert len(data["answer"]) > 0


@pytest.mark.asyncio
async def test_chat_post_empty_query_returns_422(test_config):
    """POST /chat with empty query returns 422 validation error."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"query": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_post_no_query_returns_422(test_config):
    """POST /chat without query returns 422."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_get_legacy_endpoint(test_config):
    """GET /chat?query=... works (legacy compatibility)."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed
        await client.post(
            "/upload/text",
            data={"text": "Наш email: info@company.com", "source": "contacts"},
        )
        # Query via GET
        response = await client.get("/chat", params={"query": "Какой email?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


@pytest.mark.asyncio
async def test_chat_stream_returns_sse(test_config):
    """GET /chat/stream returns SSE event stream."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed
        await client.post(
            "/upload/text",
            data={"text": "Контакты: +7 (495) 123-45-67", "source": "contacts"},
        )
        # Stream
        response = await client.get("/chat/stream", params={"query": "Телефон?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    # Should have data events
    assert "data: " in body
    # Should end with done=true
    assert '"done":true' in body or '"done": true' in body
