import asyncio
import os
from unittest.mock import AsyncMock, patch

os.environ["PYTEST_RUNNING"] = "1"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_studio_test",
)

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db():
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db):
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=hash_password("Test@12345"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={"email": "testadmin@example.com", "password": "Test@12345"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture(autouse=True)
async def mock_ai_service():
    """Mock DeepSeek API calls so tests don't need real API keys."""
    mock_generate = AsyncMock(return_value={
        "generated_text": "Mock generated content for testing.",
        "token_usage": 150,
        "generation_time_ms": 500,
    })

    async def mock_stream(text):
        for char in text:
            yield char

    mock_stream_gen = AsyncMock()
    mock_stream_gen.return_value = mock_stream("Mock streaming content.")

    with patch("app.services.ai_service.deepseek_generate", mock_generate), \
         patch("app.services.ai_service.deepseek_generate_stream", mock_stream_gen):
        yield
