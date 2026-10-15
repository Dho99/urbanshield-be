from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator


def _normalize_email(v):
    if isinstance(v, str):
        return v.strip().lower()
    return v


def _check_email_shape(v: str) -> str:
    # Sengaja longgar: terima domain dev/reserved (.local, .localhost,
    # .internal, ...) yang ditolak EmailStr/email-validator.
    local, sep, domain = v.partition("@")
    if not sep or not local or not domain or " " in v:
        raise ValueError("Enter a valid email address")
    return v


Email = Annotated[str, BeforeValidator(_normalize_email), AfterValidator(_check_email_shape)]


class UserCreate(BaseModel):
    email: Email
    password: str
    full_name: str | None = None
    role: str = "viewer"

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: Email
    password: str
