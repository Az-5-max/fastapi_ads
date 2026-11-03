from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import Base, engine, get_db
from models import Advertisement
from schemas import AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Advertisement Service")


@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201)
def create_ad(data: AdvertisementCreate, db: Session = Depends(get_db)):
    ad = Advertisement(**data.dict())
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
def update_ad(advertisement_id: int, data: AdvertisementUpdate, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(ad, field, value)

    db.commit()
    db.refresh(ad)
    return ad


@app.delete("/advertisement/{advertisement_id}")
def delete_ad(advertisement_id: int, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    db.delete(ad)
    db.commit()
    return {"message": "Удалено"}


@app.get("/advertisement", response_model=List[AdvertisementResponse])
def search_ads(
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    price: Optional[float] = Query(None),
    author: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Advertisement)

    if title:
        query = query.filter(Advertisement.title.contains(title))
    if description:
        query = query.filter(Advertisement.description.contains(description))
    if price:
        query = query.filter(Advertisement.price == price)
    if author:
        query = query.filter(Advertisement.author.contains(author))

    return query.all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)