import time

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.redis import Keys, redis_client
from app.models import User

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])


@router.post("/join")
async def join_queue(user: User = Depends(get_current_user)):
    active = await redis_client.get(Keys.active_match(user.id))
    if active:
        return {"status": "in_match", "match_id": int(active)}
    await redis_client.zadd(Keys.MM_QUEUE, {str(user.id): user.rating})
    await redis_client.hsetnx(Keys.MM_JOINED, str(user.id), time.time())
    return {"status": "searching"}


@router.post("/leave")
async def leave_queue(user: User = Depends(get_current_user)):
    await redis_client.zrem(Keys.MM_QUEUE, str(user.id))
    await redis_client.hdel(Keys.MM_JOINED, str(user.id))
    return {"status": "idle"}


@router.get("/status")
async def queue_status(user: User = Depends(get_current_user)):
    active = await redis_client.get(Keys.active_match(user.id))
    if active:
        return {"status": "in_match", "match_id": int(active)}
    in_queue = await redis_client.zscore(Keys.MM_QUEUE, str(user.id)) is not None
    waiting = await redis_client.zcard(Keys.MM_QUEUE)
    return {"status": "searching" if in_queue else "idle", "players_waiting": waiting}
