from __future__ import annotations

from typing import Any

import httpx

from seqdb_cli.config import SeqDBConfig


class SeqDBClient:
    def __init__(self, config: SeqDBConfig) -> None:
        self.config = config
        self.base_url = config.server_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    def _auth_headers(self) -> dict[str, str]:
        if self.config.access_token:
            return {"Authorization": f"Bearer {self.config.access_token}"}
        return {}

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._client.get(path, headers=self._auth_headers(), **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._client.post(path, headers=self._auth_headers(), **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._client.put(path, headers=self._auth_headers(), **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._client.delete(path, headers=self._auth_headers(), **kwargs)

    async def login(self, email: str, password: str) -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()
