from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.auth import AdminRegisterRequest, ApiKeyCreate, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        result = await self.db.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            )

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            display_name=data.display_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def register_admin(self, data: AdminRegisterRequest) -> User:
        if not settings.ADMIN_REGISTRATION_CODE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员自助注册已关闭",
            )

        if data.admin_code != settings.ADMIN_REGISTRATION_CODE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员注册码无效",
            )

        result = await self.db.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            )

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            display_name=data.display_name,
            is_superuser=True,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ── ApiKey CRUD ──

    async def save_api_key(self, user_id, data: ApiKeyCreate) -> dict:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.provider == data.provider)
        )
        key = result.scalar_one_or_none()
        if key:
            key.api_key = data.api_key
            key.base_url = data.base_url
            key.is_active = True
        else:
            key = ApiKey(
                user_id=user_id,
                provider=data.provider,
                api_key=data.api_key,
                base_url=data.base_url,
            )
            self.db.add(key)
        await self.db.flush()
        await self.db.refresh(key)
        return {
            "id": str(key.id),
            "provider": key.provider,
            "api_key_masked": "****" + key.api_key[-4:] if key.api_key and len(key.api_key) >= 4 else "****",
            "base_url": key.base_url,
            "is_active": key.is_active,
            "created_at": key.created_at.isoformat() if key.created_at else "",
        }

    async def list_api_keys(self, user_id) -> list[dict]:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        )
        keys = result.scalars().all()
        return [
            {
                "id": str(k.id),
                "provider": k.provider,
                "api_key_masked": "****" + k.api_key[-4:] if k.api_key and len(k.api_key) >= 4 else "****",
                "base_url": k.base_url,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else "",
            }
            for k in keys
        ]

    async def delete_api_key(self, user_id, key_id) -> None:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        )
        key = result.scalar_one_or_none()
        if key is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
        await self.db.delete(key)
        await self.db.flush()
