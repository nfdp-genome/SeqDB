import pytest


@pytest.mark.asyncio
async def test_get_run_not_found(client):
    response = await client.get("/api/v1/runs/NFDP-RUN-999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_runs_empty(client):
    response = await client.get("/api/v1/runs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_qc_not_found(client):
    response = await client.get("/api/v1/runs/NFDP-RUN-999999/qc")
    assert response.status_code == 404
