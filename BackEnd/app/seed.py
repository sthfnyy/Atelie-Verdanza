from sqlalchemy.orm import Session

from app.database import User
from app.security import hash_password


def create_admin_user(db: Session):
    admin_email = "admin@verdanza.com"

    existing_admin = db.query(User).filter(User.email == admin_email).first()

    if existing_admin:
        return

    admin = User(
        name="Administrador",
        email=admin_email,
        password_hash=hash_password("12345678"),
        is_admin=True,
    )

    db.add(admin)
    db.commit()