import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.ncbi.client import NCBIClient


@pytest.mark.asyncio
async def test_submit_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "SUB12345678",
        "status": "submitted",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.ncbi.client.httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_instance

        client = NCBIClient(
            base_url="https://submit.ncbi.nlm.nih.gov/api/2.0/submissions/",
            api_key="test-key",
        )
        result = await client.submit("<Submission/>", "BioProject")

    assert result["submission_id"] == "SUB12345678"
    assert result["status"] == "submitted"


@pytest.mark.asyncio
async def test_check_status():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "processed-ok",
        "actions": [
            {"id": "SUB12345678-bp", "status": "processed-ok",
             "responses": [{"accession": "PRJNA999999"}]},
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.ncbi.client.httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_instance

        client = NCBIClient(
            base_url="https://submit.ncbi.nlm.nih.gov/api/2.0/submissions/",
            api_key="test-key",
        )
        result = await client.check_status("SUB12345678")

    assert result["status"] == "processed-ok"


@pytest.mark.asyncio
async def test_submit_handles_error():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400", request=MagicMock(), response=mock_response
    )

    with patch("app.ncbi.client.httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_instance

        client = NCBIClient(
            base_url="https://submit.ncbi.nlm.nih.gov/api/2.0/submissions/",
            api_key="test-key",
        )
        result = await client.submit("<Submission/>", "BioProject")

    assert result["status"] == "error"
    assert "error" in result
