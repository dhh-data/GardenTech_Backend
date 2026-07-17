"""
api/users.py
Endpoint manajemen user, dipakai halaman pages/users.html (khusus Admin).
Semua endpoint di sini butuh login sebagai Admin (lihat require_admin).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRoleUpdate
from app.core.dependencies import require_admin, get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# GET ALL USERS (khusus Admin) - untuk tabel di halaman Manajemen User
@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.asc()).all()


# UPDATE ROLE (khusus Admin) - dropdown role di tabel manajemen user
@router.put("/{username}/role", response_model=UserResponse)
def update_user_role(
    username: str,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if payload.role not in ("Admin", "Viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role harus 'Admin' atau 'Viewer'."
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


# DELETE USER (khusus Admin) - tombol hapus di tabel manajemen user
@router.delete("/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak bisa menghapus akun yang sedang login."
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db.delete(user)
    db.commit()

    return {"message": f"User {username} berhasil dihapus"}


# GET PROFIL SENDIRI - opsional, berguna untuk validasi token di frontend
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
