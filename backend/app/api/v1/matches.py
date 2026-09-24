from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.redis import Keys, redis_client
from app.db.session import get_db
from app.models import Match, User
from app.schemas import MatchState, PlayerInfo
from app.services.battle_manager import forfeit, load_problem, problem_detail

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/{match_id}", response_model=MatchState)
async def get_match(match_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Battle page isse poora state leta hai (page refresh pe bhi kaam karta hai)."""
    match = await db.get(Match, match_id)
    if not match or user.id not in (match.player1_id, match.player2_id):
        raise HTTPException(404, "Match not found")

    is_p1 = match.player1_id == user.id
    opp = match.player2 if is_p1 else match.player1
    me = match.player1 if is_p1 else match.player2

    # Live battle ka progress Redis se, finished ka DB se
    state = await redis_client.hgetall(Keys.battle(match_id)) if match.status == "live" else {}
    if state:
        my_passed = int(state["p1_passed" if is_p1 else "p2_passed"])
        opp_passed = int(state["p2_passed" if is_p1 else "p1_passed"])
    else:
        my_passed = match.player1_passed if is_p1 else match.player2_passed
        opp_passed = match.player2_passed if is_p1 else match.player1_passed

    problem = await load_problem(db, match.problem_id)
    return MatchState(
        id=match.id, status=match.status, problem=problem_detail(problem),
        me=PlayerInfo(id=me.id, username=me.username, rating=me.rating),
        opponent=PlayerInfo(id=opp.id, username=opp.username, rating=opp.rating),
        my_passed=my_passed, opponent_passed=opp_passed, total_tests=match.total_tests,
        ends_at=match.ends_at.timestamp(), winner_id=match.winner_id, is_draw=match.is_draw,
        end_reason=match.end_reason,
        my_rating_change=match.player1_rating_change if is_p1 else match.player2_rating_change,
    )


@router.post("/{match_id}/forfeit")
async def forfeit_match(match_id: int, user: User = Depends(get_current_user)):
    if not await forfeit(match_id, user.id):
        raise HTTPException(400, "Match is not live or you are not a player")
    return {"status": "forfeited"}
