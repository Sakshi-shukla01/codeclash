"""
Battle manager: battle shuru karna, progress update karna, aur battle khatam karna.

Live battle ka state Redis mein rehta hai (fast). Battle khatam hone pe final result
PostgreSQL mein save hota hai (permanent).
"""
import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.redis import Keys, redis_client
from app.db.session import SessionLocal
from app.models import Match, Problem, TestCase, User
from app.schemas import ProblemDetail, SampleTest
from app.services.elo import rating_changes
from app.services.events import notify

log = logging.getLogger("codeclash.battle")


def problem_detail(problem: Problem) -> ProblemDetail:
    return ProblemDetail(
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        description=problem.description,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        samples=[
            SampleTest(input=t.input, expected_output=t.expected_output)
            for t in problem.test_cases
            if t.is_sample
        ],
    )


# ---------------------------------------------------------------- battle start
async def create_match(db: AsyncSession, p1_id: int, p2_id: int) -> Match:
    problem_ids = (await db.scalars(select(Problem.id))).all()
    if not problem_ids:
        raise RuntimeError("No problems in database")
    problem_id = random.choice(problem_ids)
    total = await db.scalar(select(func.count(TestCase.id)).where(TestCase.problem_id == problem_id))

    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(seconds=settings.BATTLE_DURATION_SECONDS)
    match = Match(player1_id=p1_id, player2_id=p2_id, problem_id=problem_id,
                  total_tests=total, started_at=now, ends_at=ends_at)
    db.add(match)
    await db.commit()

    ends_ts = ends_at.timestamp()
    pipe = redis_client.pipeline()
    pipe.hset(Keys.battle(match.id), mapping={
        "p1": p1_id, "p2": p2_id, "problem_id": problem_id, "total": total,
        "p1_passed": 0, "p2_passed": 0, "ends_at": ends_ts,
    })
    pipe.expire(Keys.battle(match.id), settings.BATTLE_DURATION_SECONDS + 3600)
    pipe.zadd(Keys.LIVE_BATTLES, {str(match.id): ends_ts})
    for uid in (p1_id, p2_id):
        pipe.set(Keys.active_match(uid), match.id, ex=settings.BATTLE_DURATION_SECONDS + 120)
    await pipe.execute()

    for uid in (p1_id, p2_id):
        await notify(uid, {"type": "match_found", "match_id": match.id})
    log.info("match %s started: %s vs %s on problem %s", match.id, p1_id, p2_id, problem_id)
    return match


# ---------------------------------------------------------------- progress
async def on_submission_result(match_id: int, user_id: int, verdict: str, passed: int, total: int):
    """Judge ka result aaya: player ka progress update karo, opponent ko batao, AC pe battle khatam."""
    state = await redis_client.hgetall(Keys.battle(match_id))
    if not state or await redis_client.exists(Keys.battle_done(match_id)):
        return
    if int(state["p1"]) == user_id:
        side, opponent = "p1", int(state["p2"])
    elif int(state["p2"]) == user_id:
        side, opponent = "p2", int(state["p1"])
    else:
        return

    best = max(int(state[f"{side}_passed"]), passed)  # best attempt count hota hai
    await redis_client.hset(Keys.battle(match_id), f"{side}_passed", best)
    await notify(opponent, {"type": "opponent_progress", "match_id": match_id,
                            "passed": best, "total": total, "verdict": verdict})

    if verdict == "AC":
        await finish_match(match_id, winner_id=user_id, reason="accepted")


async def notify_typing(match_id: int, user_id: int):
    state = await redis_client.hgetall(Keys.battle(match_id))
    if not state:
        return
    p1, p2 = int(state["p1"]), int(state["p2"])
    if user_id in (p1, p2):
        await notify(p2 if user_id == p1 else p1, {"type": "opponent_typing", "match_id": match_id})


# ---------------------------------------------------------------- battle end
async def finish_match(match_id: int, winner_id: int | None, reason: str):
    """
    Battle khatam karo. Race condition se bachav: agar do log ek hi millisecond mein AC karein,
    toh Redis 'SET NX' sirf pehle wale ko allow karega. Doosra call yahin return ho jaayega.
    """
    if not await redis_client.set(Keys.battle_done(match_id), "1", nx=True, ex=86400):
        return
    state = await redis_client.hgetall(Keys.battle(match_id))

    async with SessionLocal() as db:
        match = await db.get(Match, match_id)
        if not match or match.status == "finished":
            return
        users = {
            u.id: u
            for u in await db.scalars(
                select(User).where(User.id.in_([match.player1_id, match.player2_id]))
                .with_for_update().execution_options(populate_existing=True)
            )
        }
        p1, p2 = users[match.player1_id], users[match.player2_id]

        score_p1 = 0.5 if winner_id is None else (1.0 if winner_id == p1.id else 0.0)
        d1, d2 = rating_changes(p1.rating, p2.rating, score_p1)
        p1.rating += d1
        p2.rating += d2
        if winner_id is None:
            p1.draws += 1
            p2.draws += 1
        else:
            winner, loser = (p1, p2) if winner_id == p1.id else (p2, p1)
            winner.wins += 1
            loser.losses += 1

        match.status = "finished"
        match.winner_id = winner_id
        match.is_draw = winner_id is None
        match.end_reason = reason
        match.ended_at = datetime.now(timezone.utc)
        match.player1_passed = int(state.get("p1_passed", 0)) if state else 0
        match.player2_passed = int(state.get("p2_passed", 0)) if state else 0
        match.player1_rating_change = d1
        match.player2_rating_change = d2
        await db.commit()
        final = {p1.id: (d1, p1.rating), p2.id: (d2, p2.rating)}

    pipe = redis_client.pipeline()
    pipe.delete(Keys.battle(match_id))
    pipe.zrem(Keys.LIVE_BATTLES, str(match_id))
    for uid in final:
        pipe.delete(Keys.active_match(uid))
    await pipe.execute()

    for uid, (change, new_rating) in final.items():
        await notify(uid, {
            "type": "battle_end", "match_id": match_id, "winner_id": winner_id,
            "is_draw": winner_id is None, "reason": reason,
            "rating_change": change, "new_rating": new_rating,
        })
    log.info("match %s finished: winner=%s reason=%s", match_id, winner_id, reason)


async def forfeit(match_id: int, user_id: int) -> bool:
    state = await redis_client.hgetall(Keys.battle(match_id))
    if not state:
        return False
    p1, p2 = int(state["p1"]), int(state["p2"])
    if user_id not in (p1, p2):
        return False
    await finish_match(match_id, winner_id=p2 if user_id == p1 else p1, reason="forfeit")
    return True


async def timeout_loop():
    """Background task: har second check karo ki kisi battle ka time khatam toh nahi hua."""
    while True:
        token = uuid.uuid4().hex
        try:
            if await redis_client.set(Keys.LOCK_TIMEOUTS, token, nx=True, px=5000):
                try:
                    expired = await redis_client.zrangebyscore(Keys.LIVE_BATTLES, "-inf", time.time())
                    for mid in expired:
                        state = await redis_client.hgetall(Keys.battle(int(mid)))
                        if not state:
                            await redis_client.zrem(Keys.LIVE_BATTLES, mid)
                            continue
                        a, b = int(state["p1_passed"]), int(state["p2_passed"])
                        winner = int(state["p1"]) if a > b else int(state["p2"]) if b > a else None
                        await finish_match(int(mid), winner_id=winner, reason="timeout")
                finally:
                    if await redis_client.get(Keys.LOCK_TIMEOUTS) == token:
                        await redis_client.delete(Keys.LOCK_TIMEOUTS)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("timeout loop error")
        await asyncio.sleep(1)


async def load_problem(db: AsyncSession, problem_id: int) -> Problem:
    return await db.scalar(
        select(Problem).where(Problem.id == problem_id).options(selectinload(Problem.test_cases))
    )
