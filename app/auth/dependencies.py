from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.db import get_db
from app.core.security import decode_access_token
from app.auth.models import User

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    cookie_token = request.cookies.get("access_token")
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication cookie")
        
    token = cookie_token.replace("Bearer ", "")
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
        user_uuid = uuid.UUID(user_id)
    except (ValueError, uuid.UUIDError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    user = await db.get(User, user_uuid)
    if user is None:
        # FIX: 401 instead of 404
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user
