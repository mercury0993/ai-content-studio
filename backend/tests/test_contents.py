import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def content_setup(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com", "password": "password123",
    })
    token = resp.json()["access_token"]

    ws = await client.post("/api/v1/workspaces", json={"name": "Content-WS"}, headers={"Authorization": f"Bearer {token}"})
    ws_id = ws.json()["id"]

    model = await client.post("/api/v1/models", json={
        "workspace_id": ws_id, "name": "GPT-4o", "provider": "openai", "model_name": "gpt-4o",
    }, headers={"Authorization": f"Bearer {token}"})
    model_id = model.json()["id"]

    prompt = await client.post("/api/v1/prompts", json={
        "title": "P", "content": "text", "category": "marketing",
        "tags": [], "variables": [], "workspace_id": ws_id,
    }, headers={"Authorization": f"Bearer {token}"})
    prompt_id = prompt.json()["id"]

    return {"token": token, "workspace_id": ws_id, "model_id": model_id, "prompt_id": prompt_id}


@pytest.mark.asyncio
async def test_generate_content(client, content_setup):
    s = content_setup
    resp = await client.post("/api/v1/contents/generate", json={
        "workspace_id": s["workspace_id"],
        "prompt_id": s["prompt_id"],
        "model_id": s["model_id"],
        "variables_used": {},
    }, headers={"Authorization": f"Bearer {s['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "draft"
    assert data["generated_text"]
    assert data["token_usage"] > 0


@pytest.mark.asyncio
async def test_list_contents(client, content_setup):
    s = content_setup
    # Generate content first
    await client.post("/api/v1/contents/generate", json={
        "workspace_id": s["workspace_id"], "prompt_id": s["prompt_id"],
        "model_id": s["model_id"], "variables_used": {},
    }, headers={"Authorization": f"Bearer {s['token']}"})

    resp = await client.get(f"/api/v1/contents?workspace_id={s['workspace_id']}", headers={"Authorization": f"Bearer {s['token']}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_update_content(client, content_setup):
    s = content_setup
    c = await client.post("/api/v1/contents/generate", json={
        "workspace_id": s["workspace_id"], "prompt_id": s["prompt_id"],
        "model_id": s["model_id"], "variables_used": {},
    }, headers={"Authorization": f"Bearer {s['token']}"})
    c_id = c.json()["id"]

    resp = await client.put(f"/api/v1/contents/{c_id}", json={"edited_text": "manually edited"}, headers={"Authorization": f"Bearer {s['token']}"})
    assert resp.status_code == 200
    assert resp.json()["edited_text"] == "manually edited"
