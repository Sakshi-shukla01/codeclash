from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.problem import Problem
from app.models.user import User


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    player1_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    player2_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))

    status: Mapped[str] = mapped_column(String(10), default="live")  # live / finished
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_draw: Mapped[bool] = mapped_column(Boolean, default=False)
    end_reason: Mapped[str | None] = mapped_column(String(20), nullable=True)  # accepted/timeout/forfeit

    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    player1_passed: Mapped[int] = mapped_column(Integer, default=0)
    player2_passed: Mapped[int] = mapped_column(Integer, default=0)
    player1_rating_change: Mapped[int] = mapped_column(Integer, default=0)
    player2_rating_change: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    player1: Mapped[User] = relationship(foreign_keys=[player1_id], lazy="joined")
    player2: Mapped[User] = relationship(foreign_keys=[player2_id], lazy="joined")
    problem: Mapped[Problem] = relationship(lazy="joined")
