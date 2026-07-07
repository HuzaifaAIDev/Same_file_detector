from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.comparison import ComparisonJob


class ComparisonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_for_user(self, job_id: str, user_id: str) -> ComparisonJob | None:
        stmt = (
            select(ComparisonJob)
            .options(selectinload(ComparisonJob.results))
            .where(ComparisonJob.id == job_id, ComparisonJob.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[ComparisonJob]:
        stmt = (
            select(ComparisonJob)
            .where(ComparisonJob.user_id == user_id)
            .order_by(ComparisonJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())
