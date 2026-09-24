from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.redis import Keys, redis_client
from app.db.session import get_db
from app.models import Problem, Submission, User
from app.schemas import SubmissionOut, SubmitRequest
from app.services.battle_manager import load_problem
from app.services.judge_client import enqueue_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionOut, status_code=202)
async def submit(body: SubmitRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Code submit karo. Yeh turant '202 queued' return karta hai. Asli result judge chalane ke baad
    WebSocket pe 'submission_result' event se aata hai (async processing).
    """
    if body.language != "python":
        raise HTTPException(400, "Only Python is supported right now")
    if len(body.code) > settings.MAX_CODE_LENGTH:
        raise HTTPException(400, "Code too long")

    if body.match_id is not None:
        state = await redis_client.hgetall(Keys.battle(body.match_id))
        if not state or user.id not in (int(state["p1"]), int(state["p2"])):
            raise HTTPException(400, "Match is not live or you are not a player")
        problem_id = int(state["problem_id"])
    elif body.problem_slug:
        problem_id = await db.scalar(select(Problem.id).where(Problem.slug == body.problem_slug))
        if not problem_id:
            raise HTTPException(404, "Problem not found")
    else:
        raise HTTPException(400, "Give match_id or problem_slug")

    # Rate limit: ek user har few seconds mein sirf ek submission
    if not await redis_client.set(Keys.submit_cooldown(user.id), "1", nx=True, ex=settings.SUBMIT_COOLDOWN_SECONDS):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Slow down! Wait a few seconds.")

    problem = await load_problem(db, problem_id)
    sub = Submission(user_id=user.id, problem_id=problem_id, match_id=body.match_id,
                     code=body.code, language=body.language, total=len(problem.test_cases))
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    await enqueue_submission(sub, problem)
    return sub


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(submission_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await db.get(Submission, submission_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(404, "Submission not found")
    return sub
