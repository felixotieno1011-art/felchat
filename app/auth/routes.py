from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.db import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.security.ratelimit import check_rate_limit
from app.auth.schemas import RegisterIn, LoginIn
from app.auth.service import create_user, authenticate
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token", value=f"Bearer {token}",
        httponly=True, max_age=settings.JWT_EXPIRE_MINUTES * 60,
        samesite="lax", secure=settings.ENVIRONMENT == "production"
    )

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # Rate limit by IP address
    client_ip = request.client.host
    await check_rate_limit(f"auth:{client_ip}", limit=5, window=300)
    
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        user = await create_user(db, payload.email, payload.password)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered")
    token = create_access_token(subject=str(user.id))
    set_auth_cookie(response, token)
    return {"message": "Registered successfully"}

@router.post("/login")
async def login(payload: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host
    await check_rate_limit(f"auth:{client_ip}", limit=10, window=300)
    
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
