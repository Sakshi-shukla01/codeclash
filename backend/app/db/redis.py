"""
Redis connection + saari Redis keys ek jagah.

Redis mein woh data rakhte hain jo FAST aur TEMPORARY hai (live battle, queue).
Permanent data (users, matches) PostgreSQL mein jaata hai.
"""
import redis.asyncio as aioredis

from app.core.config import settings

redis_client: aioredis.Redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class Keys:
    MM_QUEUE = "mm:queue"                # Sorted Set: user_id -> rating (matchmaking waiting list)
    MM_JOINED = "mm:joined"              # Hash: user_id -> join time (range badhane ke liye)
    JUDGE_QUEUE = "judge:queue"          # List: judge worker ke liye jobs
    JUDGE_RESULTS = "judge:results"      # List: worker ke results wapas
    LIVE_BATTLES = "battles:live"        # Sorted Set: match_id -> ends_at (timeout check)
    LOCK_MATCHMAKER = "lock:matchmaker"
    LOCK_TIMEOUTS = "lock:timeouts"

    @staticmethod
    def battle(match_id: int) -> str:     # Hash: live battle state
        return f"battle:{match_id}"

    @staticmethod
    def battle_done(match_id: int) -> str:  # flag: battle ek hi baar khatam ho (race condition se bachav)
        return f"battle:{match_id}:done"

    @staticmethod
    def active_match(user_id: int) -> str:
        return f"user:{user_id}:active_match"

    @staticmethod
    def submit_cooldown(user_id: int) -> str:
        return f"user:{user_id}:cooldown"

    @staticmethod
    def user_events(user_id: int) -> str:  # Pub/Sub channel: is user ke liye live events
        return f"events:user:{user_id}"
