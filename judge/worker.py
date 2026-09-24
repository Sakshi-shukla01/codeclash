"""
Judge worker: Redis queue se submissions uthata hai, sandbox mein chalata hai,
aur result wapas Redis mein daal deta hai.

Flow:
  backend  --LPUSH-->  judge:queue  --BRPOP-->  worker  --LPUSH-->  judge:results  --> backend

Scaling: zyada load? Aur workers chalao ->  docker compose up --scale judge=4
Sab workers ek hi queue se kaam uthate hain, Redis ensure karta hai ki ek job ek hi worker ko mile.
"""
import json
import logging
import os
import signal
import time

import redis

from checker import judge
from sandbox import SandboxError, run_in_sandbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [judge] %(levelname)s %(message)s")
log = logging.getLogger("judge.worker")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUEUE = "judge:queue"
RESULTS = "judge:results"

running = True


def stop(*_):
    global running
    running = False
    log.info("shutting down after current job...")


def process(job: dict) -> dict:
    started = time.monotonic()
    try:
        result = judge(job, run=run_in_sandbox)
    except SandboxError as e:
        log.error("sandbox error for submission %s: %s", job.get("submission_id"), e)
        result = {
            "submission_id": job["submission_id"], "verdict": "IE", "passed": 0,
            "total": len(job.get("tests", [])), "runtime_ms": 0, "tests": [],
            "message": "Judge internal error, please resubmit.",
        }
    log.info(
        "submission %s -> %s (%s/%s) in %.2fs",
        job["submission_id"], result["verdict"], result["passed"], result["total"],
        time.monotonic() - started,
    )
    return result


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    while running:
        try:
            r.ping()
            break
        except redis.ConnectionError:
            log.info("waiting for redis at %s ...", REDIS_URL)
            time.sleep(2)

    log.info("judge worker ready (mode=%s), listening on '%s'", os.environ.get("JUDGE_MODE", "docker"), QUEUE)
    while running:
        try:
            item = r.brpop(QUEUE, timeout=2)
        except redis.ConnectionError:
            log.warning("lost redis connection, retrying...")
            time.sleep(2)
            continue
        if not item:
            continue
        job = json.loads(item[1])
        result = process(job)
        r.lpush(RESULTS, json.dumps(result))


if __name__ == "__main__":
    main()
