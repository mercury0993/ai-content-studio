import pytest


@pytest.fixture
async def dashboard_client(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com", "password": "password123",
    })
    token = resp.json()["access_token"]
    return client, token


@pytest.mark.asyncio
async def test_dashboard_stats(dashboard_client):
    client, token = dashboard_client
    resp = await client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total_contents" in data
    assert "pending_reviews" in data


@pytest.mark.asyncio
async def test_dashboard_trend(dashboard_client):
    client, token = dashboard_client
    resp = await client.get("/api/v1/dashboard/trend", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "dates" in data
    assert "counts" in data


@pytest.mark.asyncio
async def test_dashboard_model_usage(dashboard_client):
    client, token = dashboard_client
    resp = await client.get("/api/v1/dashboard/model-usage", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_dashboard_user_ranking(dashboard_client):
    client, token = dashboard_client
    resp = await client.get("/api/v1/dashboard/user-ranking", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_dashboard_recent(dashboard_client):
    client, token = dashboard_client
    resp = await client.get("/api/v1/dashboard/recent", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "data" in resp.json()
