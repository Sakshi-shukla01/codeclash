from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # "two-sum"
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)  # markdown
    difficulty: Mapped[str] = mapped_column(String(10))  # easy / medium / hard
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", order_by="TestCase.position", cascade="all, delete-orphan"
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)  # sample = user ko dikhega

    problem: Mapped[Problem] = relationship(back_populates="test_cases")
