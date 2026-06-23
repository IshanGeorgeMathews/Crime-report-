from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User
from app.core import security

# We extract token from Authorization header (Bearer token)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        result = await db.execute(select(User).filter(User.role == "admin"))
        user = result.scalars().first()
        if user:
            return user
    except Exception:
        pass
        
    return User(
        id="dummy-admin-id",
        username="admin",
        password_hash=security.get_password_hash("admin"),
        full_name="System Administrator (Testing)",
        role="admin",
        district="PKD",
        is_active=True
    )

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        # Everyone gets admin rights in testing phase
        return user

# Role dependencies helper
require_viewer = RoleChecker(["viewer", "analyst", "supervisor", "admin"])
require_analyst = RoleChecker(["analyst", "supervisor", "admin"])
require_supervisor = RoleChecker(["supervisor", "admin"])
require_admin = RoleChecker(["admin"])
