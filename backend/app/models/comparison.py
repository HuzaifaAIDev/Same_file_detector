import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ComparisonJob(Base):
    __tablename__ = "comparison_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    base_file_count: Mapped[int] = mapped_column(Integer, default=0)
    compare_file_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    owner = relationship("User", back_populates="comparison_jobs")
    results = relationship(
        "ComparisonResult", back_populates="job", cascade="all, delete-orphan"
    )


class ComparisonResult(Base):
    __tablename__ = "comparison_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_jobs.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(500))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="DIFFERENT")
    message: Mapped[str] = mapped_column(Text, nullable=True)

    job = relationship("ComparisonJob", back_populates="results")
