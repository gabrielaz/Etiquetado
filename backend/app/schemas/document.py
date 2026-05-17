from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.document import DocumentStatus


class DocumentOut(BaseModel):
    id: int
    project_id: int
    filename: str
    original_filename: str
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    status: DocumentStatus
    word_count: Optional[int] = 0
    labeled_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
