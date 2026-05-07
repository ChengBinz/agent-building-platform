from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str | None = None


class AdminRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str | None = None
    admin_code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None


class ApiKeyOut(BaseModel):
    id: UUID
    provider: str
    api_key_masked: str
    base_url: str | None = None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}
