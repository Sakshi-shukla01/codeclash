from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Problem
from app.schemas import ProblemDetail, ProblemSummary
from app.services.battle_manager import problem_detail

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemSummary])
async def list_problems(db: AsyncSession = Depends(get_db)):
    return (await db.scalars(select(Problem).order_by(Problem.id))).all()


@router.get("/{slug}", response_model=ProblemDetail)
async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
    problem = await db.scalar(
        select(Problem).where(Problem.slug == slug).options(selectinload(Problem.test_cases))
    )
    if not problem:
        raise HTTPException(404, "Problem not found")
    return problem_detail(problem)  # hidden tests yahan se kabhi bahar nahi jaate
