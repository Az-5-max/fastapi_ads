from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import Base, engine, get_db
from models import Advertisement, User
from schemas import (
    LoginRequest, UserCreate, UserUpdate, UserResponse,
    AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse
)
from auth import hash_password, verify_password, create_token
from dependencies import get_current_user, require_user, require_admin

from fastapi.security import HTTPBearer

security = HTTPBearer()

app = FastAPI(
    title="Advertisement Service",
    swagger_ui_parameters={"persistAuthorization": True}
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Advertisement Service")


# ========== LOGIN ==========
@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_token({"user_id": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


# ========== USERS ==========
@app.post("/user", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role or "user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/user/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.patch("/user/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if data.username:
        user.username = data.username
    if data.password:
        user.password_hash = hash_password(data.password)
    if data.role and current_user.role == "admin":
        user.role = data.role

    db.commit()
    db.refresh(user)
    return user


@app.delete("/user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db.delete(user)
    db.commit()
    return {"message": "Пользователь удалён"}


# ========== ADVERTISEMENTS ==========
@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201)
def create_ad(
    data: AdvertisementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    ad = Advertisement(**data.dict(), author_id=current_user.id)
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad


@app.get("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
def get_ad(advertisement_id: int, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ad


@app.patch("/advertisement/{advertisement_id}", response_model=AdvertisementResponse)
def update_ad(
    advertisement_id: int,
    data: AdvertisementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    ad = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if ad.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(ad, field, value)

    db.commit()
    db.refresh(ad)
    return ad


@app.delete("/advertisement/{advertisement_id}")
def delete_ad(
    advertisement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    ad = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if ad.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    db.delete(ad)
    db.commit()
    return {"message": "Удалено"}


@app.get("/advertisement", response_model=List[AdvertisementResponse])
def search_ads(
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Advertisement)

    if title:
        query = query.filter(Advertisement.title.contains(title))
    if description:
        query = query.filter(Advertisement.description.contains(description))
    if price:
        query = query.filter(Advertisement.price == price)

    return query.all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)