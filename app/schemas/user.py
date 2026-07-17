"""
schemas/user.py
Schema Pydantic untuk validasi request/response di endpoint auth & users.
Field disesuaikan ke frontend: username + password (bukan fullname/email).
"""

from datetime import datetime
from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserRoleUpdate(BaseModel):
    role: str  # "Admin" atau "Viewer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response setelah login berhasil - persis field yang dibutuhkan auth.js di frontend."""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
