import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_studio_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    """Create all tables once before all tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a session that rolls back after each test for isolation."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(conn, expire_on_commit=False)
        yield session
        await session.close()
        await trans.rollback()


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
        hashed_password=hash_password("password123"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={"email": "testadmin@example.com", "password": "password123"})
    return resp.json()["access_token"]
