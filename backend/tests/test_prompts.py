import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def workspace(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com", "password": "password123",
    })
    token = resp.json()["access_token"]
    ws = await client.post("/api/v1/workspaces", json={"name": "Prompt-WS"}, headers={"Authorization": f"Bearer {token}"})
    return {"id": ws.json()["id"], "token": token}


@pytest.mark.asyncio
async def test_create_prompt(client, workspace):
    resp = await client.post("/api/v1/prompts", json={
        "title": "Test Prompt",
        "content": "Hello {{name}}",
        "category": "marketing",
        "tags": ["test"],
        "variables": [{"name": "name", "required": True}],
        "workspace_id": workspace["id"],
    }, headers={"Authorization": f"Bearer {workspace['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Prompt"
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_list_prompts(client, workspace):
    w_id = workspace["id"]
    token = workspace["token"]

    await client.post("/api/v1/prompts", json={
        "title": "P1", "content": "c1", "category": "tech_doc",
        "tags": [], "variables": [], "workspace_id": w_id,
    }, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/prompts", json={
        "title": "P2", "content": "c2", "category": "social_media",
        "tags": [], "variables": [], "workspace_id": w_id,
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.get(f"/api/v1/prompts?workspace_id={w_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_get_prompt(client, workspace):
    token = workspace["token"]

    p = await client.post("/api/v1/prompts", json={
        "title": "P-Detail", "content": "content here", "category": "marketing",
        "tags": [], "variables": [], "workspace_id": workspace["id"],
    }, headers={"Authorization": f"Bearer {token}"})
    p_id = p.json()["id"]

    resp = await client.get(f"/api/v1/prompts/{p_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "P-Detail"


@pytest.mark.asyncio
async def test_update_prompt(client, workspace):
    token = workspace["token"]

    p = await client.post("/api/v1/prompts", json={
        "title": "Original", "content": "old", "category": "marketing",
        "tags": [], "variables": [], "workspace_id": workspace["id"],
    }, headers={"Authorization": f"Bearer {token}"})
    p_id = p.json()["id"]

    resp = await client.put(f"/api/v1/prompts/{p_id}", json={"content": "new content"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "new content"
    assert resp.json()["version"] == 2


@pytest.mark.asyncio
async def test_delete_prompt(client, workspace):
    token = workspace["token"]

    p = await client.post("/api/v1/prompts", json={
        "title": "ToDelete", "content": "x", "category": "marketing",
        "tags": [], "variables": [], "workspace_id": workspace["id"],
    }, headers={"Authorization": f"Bearer {token}"})
    p_id = p.json()["id"]

    resp = await client.delete(f"/api/v1/prompts/{p_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
