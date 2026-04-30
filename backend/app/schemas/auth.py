from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False

    model_config = {"from_attributes": True}
