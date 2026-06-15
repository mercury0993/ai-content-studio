import pytest


@pytest.mark.asyncio
async def test_create_workspace(client, admin_token, admin_user):
    resp = await client.post("/api/v1/workspaces", json={
        "name": "Test WS", "description": "desc",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test WS"
    assert data["owner_id"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_list_workspaces(client, admin_token):
    await client.post("/api/v1/workspaces", json={"name": "WS1"}, headers={"Authorization": f"Bearer {admin_token}"})
    await client.post("/api/v1/workspaces", json={"name": "WS2"}, headers={"Authorization": f"Bearer {admin_token}"})

    resp = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_workspace(client, admin_token):
    ws = await client.post("/api/v1/workspaces", json={"name": "WS-Detail"}, headers={"Authorization": f"Bearer {admin_token}"})
    ws_id = ws.json()["id"]

    resp = await client.get(f"/api/v1/workspaces/{ws_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "WS-Detail"


@pytest.mark.asyncio
async def test_update_workspace(client, admin_token):
    ws = await client.post("/api/v1/workspaces", json={"name": "Original"}, headers={"Authorization": f"Bearer {admin_token}"})
    ws_id = ws.json()["id"]

    resp = await client.put(f"/api/v1/workspaces/{ws_id}", json={"name": "Updated"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_workspace(client, admin_token):
    ws = await client.post("/api/v1/workspaces", json={"name": "ToDelete"}, headers={"Authorization": f"Bearer {admin_token}"})
    ws_id = ws.json()["id"]

    resp = await client.delete(f"/api/v1/workspaces/{ws_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
