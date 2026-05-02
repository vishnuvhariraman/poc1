from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import CaseORM


def create_case_async(screening_request_id: int, reason: str):
    db: Session = SessionLocal()
    try:
        db.add(CaseORM(screening_request_id=screening_request_id, reason=reason))
        db.commit()
    finally:
        db.close()
