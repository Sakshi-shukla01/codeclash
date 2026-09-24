"""Startup pe problems.json se problems DB mein daalna (sirf naye slugs)."""
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Problem, TestCase

log = logging.getLogger("codeclash.seed")
SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "problems.json"


async def seed_problems() -> None:
    data = json.loads(SEED_FILE.read_text())
    async with SessionLocal() as db:
        existing = set((await db.scalars(select(Problem.slug))).all())
        added = 0
        for p in data:
            if p["slug"] in existing:
                continue
            problem = Problem(
                slug=p["slug"], title=p["title"], description=p["description"],
                difficulty=p["difficulty"], time_limit_ms=p["time_limit_ms"],
                memory_limit_mb=p["memory_limit_mb"],
            )
            problem.test_cases = [
                TestCase(position=i, input=t["input"], expected_output=t["expected_output"],
                         is_sample=t["is_sample"])
                for i, t in enumerate(p["test_cases"])
            ]
            db.add(problem)
            added += 1
        await db.commit()
    if added:
        log.info("seeded %d problems", added)
