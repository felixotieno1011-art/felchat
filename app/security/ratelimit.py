from fastapi import HTTPException, status
from app.core.redis import get_redis

async def check_rate_limit(user_id: str, limit: int = 20, window: int = 60):
    redis = get_redis()
    key = f"ratelimit:{user_id}"
    
    # Increment the counter
    current = await redis.incr(key)
    
    # If it's the first request, set the expiration timer
    if current == 1:
        await redis.expire(key, window)
        
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. You can send {limit} messages per minute."
        )
