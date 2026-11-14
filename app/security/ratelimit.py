from fastapi import HTTPException, status
from app.core.redis import get_redis

# Lua script ensures INCR and EXPIRE happen atomically
LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

async def check_rate_limit(user_id: str, limit: int = 20, window: int = 60):
    redis = get_redis()
    key = f"ratelimit:{user_id}"
    
    try:
        # Run the Lua script
        current = await redis.eval(LUA_SCRIPT, 1, key, window)
    except Exception:
        # If Redis crashes, don't block the user
        return
        
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait before trying again."
        )
