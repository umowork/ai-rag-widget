import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def app():
    from main import app
    return app


@pytest.mark.asyncio
async def test_health_smoke(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_query(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/chat", params={"query": "test"})
    assert r.status_code in (200, 422)
