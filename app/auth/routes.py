from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import create_access_token
from app.auth.schemas import RegisterIn, LoginIn
from app.auth.service import create_user, authenticate
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

def set_auth_cookie(response: Response, token: str):
    # httponly=True prevents JS/XSS from reading the token
    # samesite="lax" helps prevent CSRF attacks
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=1800, # 30 minutes
        samesite="lax",
        secure=False # Set to True if you deploy to HTTPS production later
    )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, response: Response, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, payload.email, payload.password)
    token = create_access_token(subject=str(user.id))
    set_auth_cookie(response, token)
    return {"message": "Registered successfully"}

@router.post("/login")
async def login(payload: LoginIn, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(subject=str(user.id))
    set_auth_cookie(response, token)
    return {"message": "Logged in successfully"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@router.get("/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}
