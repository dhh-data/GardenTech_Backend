"""
api/auth.py
Endpoint login & register.
Prefix "/auth" supaya cocok dengan APP_CONFIG.AUTH_LOGIN_ENDPOINT
dan APP_CONFIG.AUTH_REGISTER_ENDPOINT di config.js frontend.

Bedanya dengan contoh dosen:
- field pakai username (bukan email/fullname)
- login mengembalikan JWT access_token beneran (frontend simpan di localStorage)
- akun pertama yang register otomatis jadi Admin, sisanya jadi Viewer
  (supaya selalu ada minimal 1 Admin tanpa perlu seed manual)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User

from app.schemas.user import (
    UserRegister,
    UserLogin,
    LoginResponse,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):

    existing_user = (
        db.query(User)
        .filter(User.username == payload.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar, coba username lain."
        )

    # akun pertama di sistem otomatis jadi Admin, selebihnya Viewer
    is_first_user = db.query(User).count() == 0
    role = "Admin" if is_first_user else "Viewer"

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Registrasi berhasil",
        "user_id": user.id,
        "role": user.role,
    }


@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):

    user = (
        db.query(User)
        .filter(User.username == payload.username)
        .first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun ini sudah dinonaktifkan."
        )

    token = create_access_token({"sub": user.username, "role": user.role})

    return LoginResponse(
        access_token=token,
        username=user.username,
        role=user.role,
    )
