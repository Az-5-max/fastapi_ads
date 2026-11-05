from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User
from auth import decode_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        return None

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    return user


def require_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user