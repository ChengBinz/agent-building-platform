from pydantic import BaseModel


class UserUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
