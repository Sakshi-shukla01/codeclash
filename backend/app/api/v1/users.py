from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Match, User
from app.schemas import LeaderboardEntry, MatchHistoryItem, UserOut

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/users/{user_id}/matches", response_model=list[MatchHistoryItem])
async def match_history(user_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    matches = (await db.scalars(
        select(Match)
        .where(or_(Match.player1_id == user_id, Match.player2_id == user_id))
        .order_by(desc(Match.started_at))
        .limit(min(limit, 100))
    )).unique().all()

    items = []
    for m in matches:
        is_p1 = m.player1_id == user_id
        opponent = m.player2 if is_p1 else m.player1
        if m.status != "finished":
            result = "live"
        elif m.is_draw:
            result = "draw"
        else:
            result = "win" if m.winner_id == user_id else "loss"
        items.append(MatchHistoryItem(
            id=m.id, opponent=opponent.username, problem=m.problem.title, result=result,
            rating_change=m.player1_rating_change if is_p1 else m.player2_rating_change,
            end_reason=m.end_reason, started_at=m.started_at,
        ))
    return items


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(limit: int = 50, db: AsyncSession = Depends(get_db)):
    users = (await db.scalars(
        select(User).order_by(desc(User.rating), User.id).limit(min(limit, 100))
    )).all()
    return [
        LeaderboardEntry(rank=i + 1, id=u.id, username=u.username, rating=u.rating,
                         wins=u.wins, losses=u.losses, draws=u.draws)
        for i, u in enumerate(users)
    ]
