import pytest


@pytest.mark.asyncio
async def test_create_project_unauthorized(client):
    response = await client.post("/api/v1/projects", json={
        "title": "Test Project",
        "description": "A test",
        "project_type": "WGS",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_project_authorized(client, auth_headers):
    response = await client.post("/api/v1/projects", json={
        "title": "Camel WGS Riyadh",
        "description": "WGS of dromedary camels from Riyadh",
        "project_type": "WGS",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["accession"].startswith("NFDP-PRJ-")
    assert data["title"] == "Camel WGS Riyadh"


@pytest.mark.asyncio
async def test_list_projects(client, auth_headers):
    await client.post("/api/v1/projects", json={
        "title": "Project 1",
        "description": "First project",
        "project_type": "WGS",
    }, headers=auth_headers)
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    response = await client.get("/api/v1/projects/NFDP-PRJ-999999")
    assert response.status_code == 404
