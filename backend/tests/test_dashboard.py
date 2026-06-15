import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def dashboard_client(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com", "password": "password123",
    })
    token = resp.json()["access_token"]
    ws = await client.post("/api/v1/workspaces", json={"name": "Dashboard-WS"}, headers={"Authorization": f"Bearer {token}"})
    ws_id = ws.json()["id"]
    return client, token, ws_id


@pytest.mark.asyncio
async def test_dashboard_stats(dashboard_client):
    client, token, ws_id = dashboard_client
    resp = await client.get(f"/api/v1/dashboard/stats?workspace_id={ws_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_contents" in data
    assert "pending_reviews" in data


@pytest.mark.asyncio
async def test_dashboard_trend(dashboard_client):
    client, token, ws_id = dashboard_client
    resp = await client.get(f"/api/v1/dashboard/trend?workspace_id={ws_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "dates" in data
    assert "counts" in data


@pytest.mark.asyncio
async def test_dashboard_model_usage(dashboard_client):
    client, token, ws_id = dashboard_client
    resp = await client.get(f"/api/v1/dashboard/model-usage?workspace_id={ws_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_dashboard_user_ranking(dashboard_client):
    client, token, ws_id = dashboard_client
    resp = await client.get(f"/api/v1/dashboard/user-ranking?workspace_id={ws_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_dashboard_recent(dashboard_client):
    client, token, ws_id = dashboard_client
    resp = await client.get(f"/api/v1/dashboard/recent?workspace_id={ws_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()
