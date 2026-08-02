from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.word import BBox

# ─── Tipos de región ──────────────────────────────────────────────────────────
class LayoutRegionTypeBase(BaseModel):
    name: str
    color: str = "#6366f1"
    description: Optional[str] = None
    shortcut: Optional[str] = None


class LayoutRegionTypeCreate(LayoutRegionTypeBase):
    pass


class LayoutRegionTypeUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    shortcut: Optional[str] = None


class LayoutRegionTypeOut(LayoutRegionTypeBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Regiones ─────────────────────────────────────────────────────────────────
class LayoutRegionCreate(BaseModel):
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    region_type_id: Optional[int] = None
    order_index: int = 0
    notes: Optional[str] = None


class LayoutRegionUpdate(BaseModel):
    bbox_x: Optional[float] = None
    bbox_y: Optional[float] = None
    bbox_width: Optional[float] = None
    bbox_height: Optional[float] = None
    region_type_id: Optional[int] = None
    order_index: Optional[int] = None
    notes: Optional[str] = None


class LayoutRegionOut(BaseModel):
    id: int
    document_id: int
    region_type_id: Optional[int]
    order_index: int
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    notes: Optional[str]
    source: str = "manual"
    created_at: datetime
    updated_at: datetime
    # Campos aplanados del tipo
    type_name: Optional[str] = None
    type_color: Optional[str] = None

    class Config:
        from_attributes = True

class SegmentedLayoutRegion(BaseModel):
    bbox: BBox
    region_type_name: str
    confidence: float
    order_index: int


class LayoutRegionSegmentationResult(BaseModel):
    document_id: int
    total_regions: int
    regions: list[SegmentedLayoutRegion]
