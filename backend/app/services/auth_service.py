import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceMemberRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


async def register(db: AsyncSession, req: RegisterRequest) -> User:
    if not req.username.strip() or not req.email.strip() or not req.password.strip():
        raise ValueError("Username, email and password are required")

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

    # Auto-join Default Workspace as VIEWER
    ws_result = await db.execute(select(Workspace).where(Workspace.name == "Default Workspace"))
    default_ws = ws_result.scalar_one_or_none()
    if default_ws:
        member = WorkspaceMember(
            workspace_id=default_ws.id,
            user_id=user.id,
            role=WorkspaceMemberRole.VIEWER,
        )
        db.add(member)

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


async def update_profile(db: AsyncSession, user_id: uuid.UUID, username: str | None, email: str | None) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    if email and email != user.email:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already in use")

    if username and username != user.username:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            raise ValueError("Username already in use")

    if username:
        user.username = username
    if email:
        user.email = email

    await db.flush()
    return user


async def change_password(db: AsyncSession, user_id: uuid.UUID, current_password: str, new_password: str) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    await db.flush()
