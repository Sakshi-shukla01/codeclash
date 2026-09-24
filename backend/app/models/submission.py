from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"), nullable=True, index=True)

    code: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="python")

    status: Mapped[str] = mapped_column(String(10), default="queued")  # queued / done
    verdict: Mapped[str | None] = mapped_column(String(10), nullable=True)  # AC/WA/TLE/RE/MLE/OLE/IE
    passed: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # per-test details

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
