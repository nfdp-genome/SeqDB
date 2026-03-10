# cli/tests/test_client.py
import httpx
import pytest
import respx
from seqdb_cli.client import SeqDBClient


@pytest.fixture
def client(mock_config):
    return SeqDBClient(mock_config)


@respx.mock
@pytest.mark.asyncio
async def test_get_with_auth_header(client):
    route = respx.get("https://api.seqdb.test/api/v1/projects/").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    resp = await client.get("/api/v1/projects/")
    assert resp.status_code == 200
    assert route.calls[0].request.headers["authorization"] == "Bearer test-token-123"


@respx.mock
@pytest.mark.asyncio
async def test_login(client):
    respx.post("https://api.seqdb.test/api/v1/auth/login").mock(
        return_value=httpx.Response(200, json={
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "token_type": "bearer",
            "expires_in": 3600,
        })
    )
    tokens = await client.login("user@example.com", "password123")
    assert tokens["access_token"] == "new-token"
