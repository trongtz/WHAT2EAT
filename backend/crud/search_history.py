from uuid import UUID

from sqlalchemy.orm import Session

from models.search_history import SearchHistory
from schemas.search_history import SearchHistoryCreate


def create_search_history(db: Session, payload: SearchHistoryCreate, customer_id: UUID | None) -> SearchHistory:
    history = SearchHistory(customer_id=customer_id, **payload.model_dump())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_search_history_by_customer(
    db: Session,
    customer_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[SearchHistory]:
    return (
        db.query(SearchHistory)
        .filter(SearchHistory.customer_id == customer_id)
        .order_by(SearchHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def clear_search_history(db: Session, customer_id: UUID) -> int:
    deleted_count = db.query(SearchHistory).filter(SearchHistory.customer_id == customer_id).delete()
    db.commit()
    return deleted_count
