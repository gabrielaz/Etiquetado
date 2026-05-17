from app.database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Bounding box en la imagen (píxeles)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)

    # Transcripción manual del texto manuscrito
    transcription = Column(String(512), nullable=True)

    # Confianza de la segmentación automática (0.0 - 1.0)
    confidence = Column(Float, nullable=True)

    # Fuente: "manual" o "auto" (segmentación asistida)
    source = Column(String(50), default="manual")

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="words")
    word_labels = relationship("WordLabel", back_populates="word", cascade="all, delete-orphan")
