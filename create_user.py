from database import SessionLocal, Base, engine
from models import User
from auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()
user = User(
    username="anna",
    password_hash=hash_password("12345"),
    role="admin"
)
db.add(user)
db.commit()
print("Пользователь создан!")
db.close()