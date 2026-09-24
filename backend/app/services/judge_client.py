"""
Backend <-> Judge worker ka connection (Redis lists ke through).

  enqueue_submission()  : job ko 'judge:queue' mein daalta hai
  result_consumer_loop(): 'judge:results' se results uthata hai, DB update karta hai, user ko batata hai

Pub/Sub ki jagah List kyun? List mein message tab tak rehta hai jab tak koi utha na le.
Agar backend 10 second ke liye restart ho, toh bhi results kho nahi jaate.
"""
import asyncio
import json
import logging

from app.db.redis import Keys, redis_client
from app.db.session import SessionLocal
from app.models import Problem, Submission
from app.services.battle_manager import on_submission_result
from app.services.events import notify

log = logging.getLogger("codeclash.judge_client")


async def enqueue_submission(submission: Submission, problem: Problem) -> None:
    job = {
        "submission_id": submission.id,
        "language": submission.language,
        "code": submission.code,
        "time_limit_ms": problem.time_limit_ms,
        "memory_limit_mb": problem.memory_limit_mb,
        "tests": [
            {"input": t.input, "expected": t.expected_output, "is_sample": t.is_sample}
            for t in problem.test_cases
        ],
    }
    await redis_client.lpush(Keys.JUDGE_QUEUE, json.dumps(job))


async def process_result(result: dict) -> None:
    async with SessionLocal() as db:
        sub = await db.get(Submission, result["submission_id"])
        if not sub or sub.status == "done":
            return
        sub.status = "done"
        sub.verdict = result["verdict"]
        sub.passed = result["passed"]
        sub.total = result["total"]
        sub.runtime_ms = result.get("runtime_ms")
        sub.message = result.get("message")
        sub.result = {"tests": result.get("tests", []), "details": result.get("details")}
        await db.commit()
        user_id, match_id = sub.user_id, sub.match_id

    await notify(user_id, {
        "type": "submission_result",
        "submission_id": result["submission_id"],
        "match_id": match_id,
        "verdict": result["verdict"],
        "passed": result["passed"],
        "total": result["total"],
        "runtime_ms": result.get("runtime_ms"),
        "message": result.get("message"),
        "details": result.get("details"),
        "tests": result.get("tests", []),
    })
    if match_id:
        await on_submission_result(match_id, user_id, result["verdict"], result["passed"], result["total"])


async def result_consumer_loop():
    while True:
        try:
            item = await redis_client.brpop(Keys.JUDGE_RESULTS, timeout=1)
            if item:
                await process_result(json.loads(item[1]))
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("result consumer error")
            await asyncio.sleep(1)
