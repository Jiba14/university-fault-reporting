from sqlalchemy.orm import Session
from database import SessionLocal
from user_models import User
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

db: Session = SessionLocal()

users = [
    User(
        username="student_demo",
        password=password_hash.hash("StudentDemo123!"),
        role="student"
    ),
    User(
        username="technician_demo",
        password=password_hash.hash("TechnicianDemo123!"),
        role="technician"
    ),
    User(
        username="admin_demo",
        password=password_hash.hash("AdminDemo123!"),
        role="admin"
    )
]

for user in users:
    existing = db.query(User).filter(User.username == user.username).first()

    if existing is None:
        db.add(user)

db.commit()
db.close()

print("Synthetic users created successfully")
