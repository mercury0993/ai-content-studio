# AI Content Studio — Plan 1: Project Skeleton + Auth + RBAC

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the project foundation — Docker Compose with PostgreSQL, FastAPI backend with async SQLAlchemy, Vue 3 frontend with Element Plus, and a complete auth system with JWT + RBAC.

**Architecture:** FastAPI backend serves REST API at `/api/v1/`, Vue 3 frontend served by Nginx which reverse-proxies `/api` to the backend. PostgreSQL stores all data. Docker Compose orchestrates all three services.

**Tech Stack:** Python 3.x, FastAPI, SQLAlchemy 2.0 (async), Pydantic, PostgreSQL, Vue 3, TypeScript, Element Plus, Pinia, Vue Router, Docker, Nginx

---

## File Map

### Backend

| File | Responsibility |
|------|---------------|
| `backend/pyproject.toml` | Python dependencies and project metadata |
| `backend/Dockerfile` | Backend container image |
| `backend/.env.example` | Environment variable template |
| `backend/app/__init__.py` | Package init |
| `backend/app/main.py` | FastAPI app factory, CORS, router mounting, startup seed |
| `backend/app/core/config.py` | Settings class reading from env vars |
| `backend/app/core/database.py` | Async engine + session factory |
| `backend/app/core/security.py` | JWT encode/decode, password hash/verify |
| `backend/app/api/deps.py` | get_db, get_current_user dependencies |
| `backend/app/api/v1/auth.py` | Auth endpoints (register, login, refresh, me) |
| `backend/app/models/__init__.py` | Import all models for Alembic |
| `backend/app/models/user.py` | User ORM model |
| `backend/app/schemas/auth.py` | Auth request/response Pydantic models |
| `backend/app/services/auth_service.py` | Auth business logic |
| `backend/alembic.ini` | Alembic config |
| `backend/alembic/env.py` | Alembic async migration env |
| `backend/tests/conftest.py` | Test fixtures (async client, test DB) |
| `backend/tests/test_auth.py` | Auth endpoint tests |

### Frontend

| File | Responsibility |
|------|---------------|
| `frontend/package.json` | Node dependencies |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/vite.config.ts` | Vite config with proxy |
| `frontend/index.html` | HTML entry |
| `frontend/Dockerfile` | Build + Nginx serve |
| `frontend/nginx.conf` | Nginx config, reverse proxy `/api` |
| `frontend/src/main.ts` | Vue app entry |
| `frontend/src/App.vue` | Root component with router-view |
| `frontend/src/router/index.ts` | Route definitions + navigation guard |
| `frontend/src/stores/user.ts` | Pinia user store (token, profile, login/logout) |
| `frontend/src/api/request.ts` | Axios instance with interceptors |
| `frontend/src/api/auth.ts` | Auth API calls |
| `frontend/src/utils/permission.ts` | Role-based menu/button permission helpers |
| `frontend/src/views/Login.vue` | Login page |
| `frontend/src/views/Register.vue` | Registration page |
| `frontend/src/views/Dashboard.vue` | Placeholder dashboard (redirects after login) |
| `frontend/src/layouts/MainLayout.vue` | Sidebar + topbar layout shell |

### Root

| File | Responsibility |
|------|---------------|
| `docker-compose.yml` | Three services: postgres, backend, frontend |
| `.gitignore` | Ignore node_modules, __pycache__, .env, dist |

---

## Task 1: Project Skeleton — Docker Compose + PostgreSQL

**Files:**
- Create: `docker-compose.yml`
- Create: `.gitignore`
- Create: `backend/.env.example`
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.pyc
.env
.venv/
*.egg-info/

# Node
node_modules/
frontend/dist/

# IDE
.vscode/
.idea/

# Docker
postgres_data/
```

- [ ] **Step 2: Create backend .env.example**

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ai_content_studio
SECRET_KEY=change-me-to-a-random-string-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_content_studio
```

- [ ] **Step 3: Create backend Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -e ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_content_studio
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

- [ ] **Step 5: Initialize git repo**

```bash
cd E:/lx/projects/ai-content-studio
git init
git add .
git commit -m "chore: project skeleton with docker-compose"
```

---

## Task 2: Backend Core — Config + Database + Security

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/security.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ai-content-studio"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "alembic>=1.14.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_content_studio"
    SECRET_KEY: str = "change-me-to-a-random-string-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 3: Create database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: Create security.py**

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/core/
git commit -m "feat: backend core — config, database, security"
```

---

## Task 3: User Model + Alembic Migrations

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)

- [ ] **Step 1: Create User model**

`backend/app/models/__init__.py`:
```python
from app.models.user import User

__all__ = ["User"]
```

`backend/app/models/user.py`:
```python
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Initialize Alembic**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic init alembic
```

- [ ] **Step 3: Configure alembic.ini**

Edit `backend/alembic.ini` — set `sqlalchemy.url` to empty (we'll set it in env.py):
```ini
[alembic]
script_location = alembic
sqlalchemy.url =
```

- [ ] **Step 4: Configure alembic/env.py for async**

Replace `backend/alembic/env.py` with:
```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.models import *  # noqa: F401,F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 5: Generate initial migration**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "create users table"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/ backend/alembic.ini backend/alembic/
git commit -m "feat: user model and alembic migration setup"
```

---

## Task 4: Auth Schemas + Service + API

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create auth schemas**

`backend/app/schemas/__init__.py`: empty file

`backend/app/schemas/auth.py`:
```python
import uuid
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create auth service**

`backend/app/services/__init__.py`: empty file

`backend/app/services/auth_service.py`:
```python
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse


async def register(db: AsyncSession, req: RegisterRequest) -> User:
    existing = await db.execute(select(User).where((User.email == req.email) | (User.username == req.username)))
    if existing.scalar_one_or_none():
        raise ValueError("Email or username already exists")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=UserRole.VIEWER,
    )
    db.add(user)
    await db.flush()
    return user


async def login(db: AsyncSession, req: LoginRequest) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise ValueError("Account is disabled")

    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


async def refresh(db: AsyncSession, token: str) -> TokenResponse:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise ValueError("User not found or disabled")

    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


async def get_me(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")
    return user
```

- [ ] **Step 3: Create API dependencies**

`backend/app/api/__init__.py`: empty file
`backend/app/api/v1/__init__.py`: empty file

`backend/app/api/deps.py`:
```python
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from sqlalchemy import select

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")
    return user
```

- [ ] **Step 4: Create auth router**

`backend/app/api/v1/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.register(db, req)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.login(db, req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.refresh(db, req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 5: Create FastAPI main app**

`backend/app/main.py`:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.database import async_session, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.api.v1.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default admin
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.commit()

    yield


app = FastAPI(title="AI Content Studio", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Copy .env.example to .env**

```bash
cp backend/.env.example backend/.env
```

- [ ] **Step 7: Build and test**

```bash
cd E:/lx/projects/ai-content-studio
docker compose up -d --build
# Wait for services to start, then:
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
# Expected: {"access_token":"...","refresh_token":"...","token_type":"bearer"}
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/ backend/.env
git commit -m "feat: auth system — register, login, refresh, JWT + RBAC roles"
```

---

## Task 5: Auth Tests

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Create test fixtures**

`backend/tests/__init__.py`: empty file

`backend/tests/conftest.py`:
```python
import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_studio_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
```

- [ ] **Step 2: Write auth tests**

`backend/tests/test_auth.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert data["role"] == "viewer"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/v1/auth/register", json={
        "username": "dup",
        "email": "dup@example.com",
        "password": "pass123",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "username": "dup",
        "email": "dup@example.com",
        "password": "pass123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client, admin_token):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "testadmin@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_refresh(client, admin_user):
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "testadmin@example.com",
        "password": "password123",
    })
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

- [ ] **Step 3: Run tests**

```bash
cd E:/lx/projects/ai-content-studio/backend
# Create test database first
docker compose exec postgres psql -U postgres -c "CREATE DATABASE ai_content_studio_test;"
pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: auth endpoint tests"
```

---

## Task 6: Frontend Skeleton — Vue 3 + Element Plus + Router

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/env.d.ts`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "ai-content-studio-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "element-plus": "^2.8.0",
    "axios": "^1.7.0",
    "echarts": "^5.5.0",
    "vue-echarts": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0",
    "@types/node": "^22.0.0",
    "unplugin-auto-import": "^0.18.0",
    "unplugin-vue-components": "^0.27.0"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({ resolvers: [ElementPlusResolver()] }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"]
    },
    "baseUrl": "."
  },
  "include": ["src/**/*.ts", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Content Studio</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 5: Create src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 6: Create src/App.vue**

```vue
<script setup lang="ts">
</script>

<template>
  <router-view />
</template>
```

- [ ] **Step 7: Create src/env.d.ts**

```typescript
/// <reference types="vite/client" />
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 8: Create Dockerfile + nginx.conf**

`frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

`frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 9: Install dependencies and verify build**

```bash
cd E:/lx/projects/ai-content-studio/frontend
npm install
npm run dev
# Open http://localhost:5173, should see blank page with no errors
```

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: frontend skeleton — Vue 3 + Element Plus + Vite"
```

---

## Task 7: Frontend Auth — Login/Register + Router + Store

**Files:**
- Create: `frontend/src/api/request.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/stores/user.ts`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/Register.vue`
- Create: `frontend/src/views/Dashboard.vue`
- Create: `frontend/src/layouts/MainLayout.vue`
- Create: `frontend/src/utils/permission.ts`

- [ ] **Step 1: Create axios request wrapper**

`frontend/src/api/request.ts`:
```typescript
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(error.response?.data?.detail || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 2: Create auth API**

`frontend/src/api/auth.ts`:
```typescript
import request from './request'

export function login(email: string, password: string) {
  return request.post('/auth/login', { email, password })
}

export function register(username: string, email: string, password: string) {
  return request.post('/auth/register', { username, email, password })
}

export function refreshToken(refresh_token: string) {
  return request.post('/auth/refresh', { refresh_token })
}

export function getMe() {
  return request.get('/auth/me')
}
```

- [ ] **Step 3: Create user store**

`frontend/src/stores/user.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import router from '@/router'

export interface UserInfo {
  id: string
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  async function login(email: string, password: string) {
    const data: any = await loginApi(email, password)
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function fetchUser() {
    const data: any = await getMe()
    userInfo.value = data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  return { token, userInfo, login, fetchUser, logout }
})
```

- [ ] **Step 4: Create router with permission guard**

`frontend/src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.public) {
    next()
    return
  }

  if (!userStore.token) {
    next('/login')
    return
  }

  if (!userStore.userInfo) {
    try {
      await userStore.fetchUser()
    } catch {
      next('/login')
      return
    }
  }

  next()
})

export default router
```

- [ ] **Step 5: Create Login.vue**

`frontend/src/views/Login.vue`:
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()

const form = ref({ email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.value.email || !form.value.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(form.value.email, form.value.password)
    ElMessage.success('登录成功')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>AI Content Studio</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.email" placeholder="邮箱" prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width:100%">登录</el-button>
        </el-form-item>
        <div style="text-align:center">
          <router-link to="/register">没有账号？注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 400px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
}
</style>
```

- [ ] **Step 6: Create Register.vue**

`frontend/src/views/Register.vue`:
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = ref({ username: '', email: '', password: '' })
const loading = ref(false)

async function handleRegister() {
  if (!form.value.username || !form.value.email || !form.value.password) {
    ElMessage.warning('请填写所有字段')
    return
  }
  loading.value = true
  try {
    await register(form.value.username, form.value.email, form.value.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>注册账号</h2>
      <el-form @submit.prevent="handleRegister">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.email" placeholder="邮箱" prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width:100%">注册</el-button>
        </el-form-item>
        <div style="text-align:center">
          <router-link to="/login">已有账号？登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 400px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
}
</style>
```

- [ ] **Step 7: Create Dashboard placeholder**

`frontend/src/views/Dashboard.vue`:
```vue
<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div>
    <h2>数据看板</h2>
    <p>欢迎, {{ userStore.userInfo?.username }}！</p>
    <p>角色: {{ userStore.userInfo?.role }}</p>
  </div>
</template>
```

- [ ] **Step 8: Create MainLayout**

`frontend/src/layouts/MainLayout.vue`:
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const isCollapse = ref(false)

function handleLogout() {
  userStore.logout()
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '200px'" style="background: #304156">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold;">
        <span v-if="!isCollapse">AI Studio</span>
        <span v-else>AI</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #eee;">
        <el-icon style="cursor: pointer; font-size: 20px" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <el-dropdown @command="handleLogout">
          <span style="cursor: pointer">
            {{ userStore.userInfo?.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
```

- [ ] **Step 9: Create permission utility**

`frontend/src/utils/permission.ts`:
```typescript
import { useUserStore } from '@/stores/user'

const roleMenus: Record<string, string[]> = {
  admin: ['/dashboard', '/workspaces', '/prompts', '/contents', '/reviews', '/models', '/settings'],
  editor: ['/dashboard', '/prompts', '/contents', '/reviews'],
  viewer: ['/dashboard', '/contents'],
}

export function hasPermission(path: string): boolean {
  const userStore = useUserStore()
  if (!userStore.userInfo) return false
  const allowed = roleMenus[userStore.userInfo.role] || []
  return allowed.some((p) => path.startsWith(p))
}

export function canEdit(): boolean {
  const userStore = useUserStore()
  return userStore.userInfo?.role === 'admin' || userStore.userInfo?.role === 'editor'
}
```

- [ ] **Step 10: Verify full auth flow**

```bash
cd E:/lx/projects/ai-content-studio
docker compose up -d --build
# Open http://localhost
# Should see login page
# Login with admin@example.com / admin123
# Should redirect to dashboard showing "欢迎, admin"
```

- [ ] **Step 11: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend auth — login, register, router guard, layout shell"
```

---

## Plan 1 Complete

After this plan, you have:
- Docker Compose with PostgreSQL + FastAPI + Vue/Nginx
- User registration, login, JWT auth
- Three roles (admin/editor/viewer) in the database
- Frontend login/register pages with router guards
- Sidebar layout shell ready for adding more menu items
- Backend tests passing
- Default admin account seeded

**Next: Plan 2 — Workspace + Prompt Management**
