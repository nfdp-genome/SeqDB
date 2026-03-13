"""NCBI Submission Portal API client."""

import httpx


class NCBIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def submit(self, xml_content: str, submission_type: str) -> dict:
        """Submit XML to NCBI Submission Portal.

        Returns:
            {"submission_id": "SUB...", "status": "submitted"}
            or {"status": "error", "error": "..."}
        """
        headers = {"Content-Type": "application/xml"}
        if self.api_key:
            headers["api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/",
                    content=xml_content,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "submission_id": data.get("id", ""),
                    "status": data.get("status", "submitted"),
                }
            except httpx.HTTPStatusError as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "detail": e.response.text if e.response else "",
                }
            except httpx.HTTPError as e:
                return {"status": "error", "error": str(e)}

    async def check_status(self, submission_id: str) -> dict:
        """Check the status of a pending NCBI submission.

        Returns the full status response from NCBI.
        """
        headers = {}
        if self.api_key:
            headers["api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/{submission_id}",
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as e:
                return {"status": "error", "error": str(e)}
