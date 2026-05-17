from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class WordLabelOut(BaseModel):
    id: int
    label_schema_id: int
    label_name: Optional[str] = None
    label_color: Optional[str] = None

    class Config:
        from_attributes = True


class WordBase(BaseModel):
    transcription: Optional[str] = None
    notes: Optional[str] = None
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    order_index: int = 0


class WordCreate(WordBase):
    source: str = "manual"
    confidence: Optional[float] = None


class WordUpdate(BaseModel):
    transcription: Optional[str] = None
    notes: Optional[str] = None
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    order_index: Optional[int] = None


class WordOut(WordBase):
    id: int
    document_id: int
    source: str
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    labels: List[WordLabelOut] = []

    class Config:
        from_attributes = True


class WordBulkCreate(BaseModel):
    """Para importar múltiples palabras desde segmentación asistida."""
    words: List[WordCreate]


# Schema para resultado de segmentación asistida
class SegmentedWord(BaseModel):
    bbox: BBox
    confidence: float
    order_index: int


class SegmentationResult(BaseModel):
    document_id: int
    total_words: int
    words: List[SegmentedWord]
    method: str  # "opencv_contour", "projection", etc.
