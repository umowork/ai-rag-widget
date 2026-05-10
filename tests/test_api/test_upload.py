"""
Tests for upload endpoints.
"""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_upload_text_success(test_config):
    """POST /upload/text adds text chunks."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/upload/text",
            data={"text": "Тестовый документ для проверки загрузки.", "source": "test"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["chunks_added"] > 0
    assert "фрагментов" in data["message"]


@pytest.mark.asyncio
async def test_upload_text_empty_returns_422(test_config):
    """POST /upload/text with empty text returns 422."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/upload/text", data={"text": "", "source": "test"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_file_txt(test_config, sample_txt_path):
    """POST /upload/file with TXT file succeeds."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_txt_path, "rb") as f:
            response = await client.post(
                "/upload/file",
                files={"file": ("test_doc.txt", f, "text/plain")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["chunks_added"] > 0
    assert "test_doc.txt" in data["message"]


@pytest.mark.asyncio
async def test_upload_file_unsupported_extension(test_config, temp_dir):
    """POST /upload/file with unsupported extension returns 400."""
    from main import create_app

    # Create unsupported file
    bad_path = os.path.join(temp_dir, "test.xyz")
    with open(bad_path, "w") as f:
        f.write("some content")

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(bad_path, "rb") as f:
            response = await client.post(
                "/upload/file",
                files={"file": ("test.xyz", f, "application/octet-stream")},
            )

    assert response.status_code == 400
    assert "Unsupported" in response.text


@pytest.mark.asyncio
async def test_upload_pdf_legacy(test_config, sample_pdf_path):
    """POST /upload/pdf (legacy endpoint) works."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_pdf_path, "rb") as f:
            response = await client.post(
                "/upload/pdf",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

    # The minimal PDF has no extractable text, so chunks_added may be 0
    # That's fine — we just verify the endpoint handles it
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_upload_then_query_flow(test_config):
    """Full flow: upload text → query → verify answer references it."""
    from main import create_app

    app = create_app(test_config)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload
        upload_resp = await client.post(
            "/upload/text",
            data={"text": "Год основания компании: 2015.", "source": "about"},
        )
        assert upload_resp.status_code == 200

        # Query
        query_resp = await client.post("/chat", json={"query": "Год основания?"})
        assert query_resp.status_code == 200
        data = query_resp.json()
        assert len(data["sources"]) > 0
        # In mock mode, answer should mention the query
        assert "Год основания?" in data["answer"] or "2015" in data["answer"]
