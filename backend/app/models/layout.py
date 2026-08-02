from app.database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class LayoutRegionType(Base):
    """Tipo de región de layout: texto principal, notas al margen, firma, etc."""
    __tablename__ = "layout_region_types"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)        # ej: "Texto principal"
    color = Column(String(7), nullable=False, default="#6366f1")
    description = Column(String(255), nullable=True)
    shortcut = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="layout_region_types")
    regions = relationship("LayoutRegion", back_populates="region_type", cascade="all, delete-orphan")


class LayoutRegion(Base):
    """Región anotada en un documento para análisis de layout."""
    __tablename__ = "layout_regions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    region_type_id = Column(Integer, ForeignKey("layout_region_types.id"), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)

    # Bounding box en píxeles
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)

    notes = Column(Text, nullable=True)
    source = Column(String(50), default="manual")  # 'manual' | 'auto' (ML)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="layout_regions")
    region_type = relationship("LayoutRegionType", back_populates="regions")
