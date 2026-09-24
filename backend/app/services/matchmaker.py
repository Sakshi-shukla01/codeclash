"""
Matchmaker: queue mein baithe players ke liye barabar rating wala opponent dhoondhna.

Rule: shuru mein ±100 rating ka opponent. Har 5 second wait karne pe range +50 badhti hai
(max ±500), taaki kisi ko bahut der wait na karna pade.
"""
import asyncio
import logging
import time
import uuid

from app.db.redis import Keys, redis_client
from app.db.session import SessionLocal
from app.services.battle_manager import create_match

log = logging.getLogger("codeclash.matchmaker")

BASE_RANGE, RANGE_STEP, MAX_RANGE = 100, 50, 500


def allowed_range(waited_seconds: float) -> int:
    return min(BASE_RANGE + RANGE_STEP * int(waited_seconds // 5), MAX_RANGE)


def find_pairs(players: list[tuple[int, int, float]], now: float) -> list[tuple[int, int]]:
    """
    players: [(user_id, rating, joined_at), ...]
    Rating se sort karke, pados wale players ko pair karte hain (greedy). O(n log n).
    Yeh pure function hai (koi Redis/DB nahi), isliye iska unit test aasaan hai.
    """
    players = sorted(players, key=lambda p: p[1])
    pairs, i = [], 0
    while i < len(players) - 1:
        a, b = players[i], players[i + 1]
        limit = max(allowed_range(now - a[2]), allowed_range(now - b[2]))
        if b[1] - a[1] <= limit:
            pairs.append((a[0], b[0]))
            i += 2
        else:
            i += 1
    return pairs


async def run_round():
    entries = await redis_client.zrange(Keys.MM_QUEUE, 0, -1, withscores=True)
    if len(entries) < 2:
        return
    joined = await redis_client.hgetall(Keys.MM_JOINED)
    now = time.time()
    players = [(int(uid), int(score), float(joined.get(uid, now))) for uid, score in entries]

    for a, b in find_pairs(players, now):
        # dono abhi bhi queue mein hain? (beech mein kisi ne "leave" toh nahi kiya)
        if None in await redis_client.zmscore(Keys.MM_QUEUE, [a, b]):
            continue
        await redis_client.zrem(Keys.MM_QUEUE, a, b)
        await redis_client.hdel(Keys.MM_JOINED, a, b)
        async with SessionLocal() as db:
            await create_match(db, a, b)


async def matchmaker_loop():
    """
    Background task, har 1 second. Redis lock isliye ki agar backend ke 3 copies chal rahi hain,
    toh ek time pe sirf ek hi matchmaking kare (warna ek player do matches mein chala jaata).
    """
    while True:
        token = uuid.uuid4().hex
        try:
            if await redis_client.set(Keys.LOCK_MATCHMAKER, token, nx=True, px=5000):
                try:
                    await run_round()
                finally:
                    if await redis_client.get(Keys.LOCK_MATCHMAKER) == token:
                        await redis_client.delete(Keys.LOCK_MATCHMAKER)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("matchmaker error")
        await asyncio.sleep(1)
