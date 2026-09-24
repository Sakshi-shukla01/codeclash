"""
CodeClash backend ka entry point.

Chalao:  uvicorn app.main:app --reload
Docs:    http://localhost:8000/docs   (saari APIs yahan se test kar sakte ho)
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401  (tables register karne ke liye)
from app.api.v1 import api_router
from app.api.v1.ws import router as ws_router
from app.core.config import settings
from app.db.redis import redis_client
from app.db.session import Base, engine
from app.services.battle_manager import timeout_loop
from app.services.events import pubsub_listener
from app.services.judge_client import result_consumer_loop
from app.services.matchmaker import matchmaker_loop
from app.services.seed import seed_problems

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
log = logging.getLogger("codeclash")


async def wait_for_services(retries: int = 30):
    """Docker mein Postgres/Redis thoda late start hote hain, isliye retry karte hain."""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await redis_client.ping()
            return
        except Exception as e:
            log.info("waiting for postgres/redis (%d/%d): %s", attempt, retries, e.__class__.__name__)
            await asyncio.sleep(2)
    raise RuntimeError("Postgres/Redis not reachable. Check DATABASE_URL and REDIS_URL.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.JWT_SECRET.startswith("dev-secret"):
        log.warning("⚠️  Default JWT_SECRET in use. Set a random JWT_SECRET in .env before deploying!")
    await wait_for_services()
    async with engine.begin() as conn:
        # Simple setup: tables auto-create. (Next step: Alembic migrations, README dekho)
        await conn.run_sync(Base.metadata.create_all)
    await seed_problems()

    # Background tasks: yeh app ke saath hamesha chalte rehte hain
    tasks = [
        asyncio.create_task(pubsub_listener(), name="pubsub"),
        asyncio.create_task(matchmaker_loop(), name="matchmaker"),
        asyncio.create_task(result_consumer_loop(), name="judge-results"),
        asyncio.create_task(timeout_loop(), name="battle-timeouts"),
    ]
    log.info("CodeClash backend ready 🚀")
    yield
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health", tags=["health"])
async def health():
    status = {"api": "ok"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception:
        status["postgres"] = "down"
    try:
        await redis_client.ping()
        status["redis"] = "ok"
        status["judge_queue_length"] = await redis_client.llen("judge:queue")
    except Exception:
        status["redis"] = "down"
    return status
