import pytest


@pytest.mark.asyncio
async def test_search_projects(client, auth_headers):
    await client.post("/api/v1/projects", json={
        "title": "Dromedary Camel WGS",
        "description": "Riyadh region camels",
        "project_type": "WGS",
    }, headers=auth_headers)

    response = await client.get("/api/v1/search?q=Dromedary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["results"][0]["type"] == "project"


@pytest.mark.asyncio
async def test_search_no_results(client):
    response = await client.get("/api/v1/search?q=nonexistent_xyz")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_checklists(client):
    response = await client.get("/api/v1/checklists")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


@pytest.mark.asyncio
async def test_get_checklist_schema(client):
    response = await client.get("/api/v1/checklists/ERC000055/schema")
    assert response.status_code == 200
    data = response.json()
    assert "required" in data
    assert "organism" in data["required"]


@pytest.mark.asyncio
async def test_get_checklist_not_found(client):
    response = await client.get("/api/v1/checklists/UNKNOWN/schema")
    assert response.status_code == 404
