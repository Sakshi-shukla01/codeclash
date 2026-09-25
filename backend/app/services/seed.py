"""
Startup pe problems.json ko database ke saath sync karna.
  - naya slug      -> problem + test cases add hote hain
  - existing slug  -> title/description/difficulty/limits update hote hain (test cases same rehte hain)
"""
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Problem, TestCase

log = logging.getLogger("codeclash.seed")
SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "problems.json"


async def seed_problems() -> None:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    async with SessionLocal() as db:
        existing = {p.slug: p for p in (await db.scalars(select(Problem))).all()}
        added = updated = 0
        for p in data:
            fields = {
                "title": p["title"], "description": p["description"], "difficulty": p["difficulty"],
                "time_limit_ms": p["time_limit_ms"], "memory_limit_mb": p["memory_limit_mb"],
            }
            problem = existing.get(p["slug"])
            if problem:
                if any(getattr(problem, k) != v for k, v in fields.items()):
                    for k, v in fields.items():
                        setattr(problem, k, v)
                    updated += 1
                continue
            problem = Problem(slug=p["slug"], **fields)
            problem.test_cases = [
                TestCase(position=i, input=t["input"], expected_output=t["expected_output"],
                         is_sample=t["is_sample"])
                for i, t in enumerate(p["test_cases"])
            ]
            db.add(problem)
            added += 1
        await db.commit()
    if added or updated:
        log.info("problems synced: %d added, %d updated", added, updated)
