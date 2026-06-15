from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceMemberRole
from app.models.ai_model import AIModel
from app.models.prompt import Prompt, PromptVersion
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.models import router as models_router
from app.api.v1.contents import router as contents_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.dashboard import router as dashboard_router
import logging
import os
import time

from app.api.v1.export import router as export_router
from app.core.logging import setup_logging

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default admin
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.commit()

    # Seed default workspace, AI model, and sample prompts
    async with async_session() as db:
        result = await db.execute(select(Workspace).where(Workspace.name == "Default Workspace"))
        if not result.scalar_one_or_none():
            admin_user_seed = (await db.execute(select(User).where(User.email == "admin@example.com"))).scalar_one()
            ws = Workspace(name="Default Workspace", description="默认工作空间", owner_id=admin_user_seed.id)
            db.add(ws)
            await db.flush()

            member = WorkspaceMember(workspace_id=ws.id, user_id=admin_user_seed.id, role=WorkspaceMemberRole.ADMIN)
            db.add(member)

            model = AIModel(
                workspace_id=ws.id, name="GPT-4o (Mock)", provider="openai",
                model_name="gpt-4o", is_active=True,
                default_params={"temperature": 0.7, "max_tokens": 2000},
            )
            db.add(model)

            # Sample prompts with variables
            prompts_data = [
                {
                    "title": "产品营销文案",
                    "content": "请为 {{product_name}} 写一段面向 {{target_audience}} 的营销文案，突出产品的核心优势。",
                    "category": "marketing",
                    "tags": ["营销", "文案"],
                    "variables": [{"name": "product_name", "required": True}, {"name": "target_audience", "required": True}],
                },
                {
                    "title": "技术文档生成",
                    "content": "请为 {{product_name}} 编写一份技术架构文档，包含系统概述、技术栈、架构设计和部署方案。",
                    "category": "tech_doc",
                    "tags": ["技术", "文档"],
                    "variables": [{"name": "product_name", "required": True}],
                },
                {
                    "title": "社交媒体帖子",
                    "content": "请为 {{product_name}} 写一条面向 {{target_audience}} 的社交媒体推广帖子，包含 emoji 和话题标签。",
                    "category": "social_media",
                    "tags": ["社交媒体", "推广"],
                    "variables": [{"name": "product_name", "required": True}, {"name": "target_audience", "required": True}],
                },
            ]
            for pd in prompts_data:
                p = Prompt(
                    workspace_id=ws.id, title=pd["title"], content=pd["content"],
                    category=pd["category"], tags=pd["tags"], variables=pd["variables"],
                    version=1, created_by=admin_user_seed.id,
                )
                db.add(p)
                await db.flush()
                db.add(PromptVersion(prompt_id=p.id, version=1, content=pd["content"]))

            await db.commit()

    yield


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

setup_logging()
logger = logging.getLogger("ai-content-studio")

app = FastAPI(title="AI Content Studio", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={
            "extra": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        },
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(prompts_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(contents_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
