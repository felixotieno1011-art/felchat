from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User
from app.core.security import hash_password, verify_password

async def create_user(db: AsyncSession, email: str, password: str) -> User:
    # FIX: Lowercase email on save
    clean_email = email.strip().lower()
    user = User(email=clean_email, hashed_password=hash_password(password))
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    # FIX: Lowercase email on lookup
    clean_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == clean_email))
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        return user
    return None
