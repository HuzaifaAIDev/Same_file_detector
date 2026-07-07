from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.otp import OTPVerification


class OTPRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self, email: str, purpose: str) -> OTPVerification | None:
        stmt = (
            select(OTPVerification)
            .where(
                OTPVerification.email == email.lower(),
                OTPVerification.purpose == purpose,
            )
            .order_by(OTPVerification.created_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def create(self, **kwargs) -> OTPVerification:
        otp = OTPVerification(**kwargs)
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp

    def save(self, otp: OTPVerification) -> None:
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)

    def delete(self, otp: OTPVerification) -> None:
        self.db.delete(otp)
        self.db.commit()
