from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.dataset import Dataset
from app.services.dataset_service import list_datasets

router = APIRouter()


@router.get("", summary="Dataset registry")
def list_all(source: str | None = Query(default=None), db: Session = Depends(get_db)):
    try:
        q = db.query(Dataset)
        if source:
            q = q.filter(Dataset.source.ilike(source))
        rows = q.all()
        if rows:
            return [{"id": r.id, "name": r.name, "source": r.source, "description": r.description, "last_update": r.last_update, "completeness": r.completeness, "record_count": r.record_count} for r in rows]
    except Exception:
        pass
    return list_datasets(source=source)
