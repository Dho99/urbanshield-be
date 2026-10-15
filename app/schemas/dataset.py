from pydantic import BaseModel
from datetime import datetime

class DatasetOut(BaseModel):
    id: int
    name: str
    source: str
    description: str | None = None
    last_update: datetime | None = None
    completeness: float | None = None
    record_count: int | None = None
    class Config:
        from_attributes = True
