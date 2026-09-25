"""
Pydantic schemas: request/response ka format.
FastAPI inse automatically validation karta hai aur /docs pe documentation banata hai.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ------------------------------------------------------------------ auth / users
class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    rating: int
    wins: int
    losses: int
    draws: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------------ problems
class SampleTest(BaseModel):
    input: str
    expected_output: str


class ProblemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str
    title: str
    difficulty: str


class ProblemDetail(ProblemSummary):
    description: str
    time_limit_ms: int
    memory_limit_mb: int
    samples: list[SampleTest]


# ------------------------------------------------------------------ submissions
class SubmitRequest(BaseModel):
    code: str = Field(min_length=1)
    # Supported languages (judge/sandbox/python/runner.py ke LANGUAGES se match karna chahiye)
    language: Literal["python", "cpp", "c", "java", "javascript"] = "python"
    match_id: int | None = None       # battle ke andar submit
    problem_slug: str | None = None   # practice mode submit


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    verdict: str | None
    passed: int
    total: int
    runtime_ms: int | None
    message: str | None
    result: dict | None
    match_id: int | None
    created_at: datetime


# ------------------------------------------------------------------ matches
class PlayerInfo(BaseModel):
    id: int
    username: str
    rating: int


class MatchState(BaseModel):
    id: int
    status: str
    problem: ProblemDetail
    me: PlayerInfo
    opponent: PlayerInfo
    my_passed: int
    opponent_passed: int
    total_tests: int
    ends_at: float  # unix timestamp (seconds)
    winner_id: int | None = None
    is_draw: bool = False
    end_reason: str | None = None
    my_rating_change: int = 0


class MatchHistoryItem(BaseModel):
    id: int
    opponent: str
    problem: str
    result: str  # win / loss / draw / live
    rating_change: int
    end_reason: str | None
    started_at: datetime


class LeaderboardEntry(BaseModel):
    rank: int
    id: int
    username: str
    rating: int
    wins: int
    losses: int
    draws: int
