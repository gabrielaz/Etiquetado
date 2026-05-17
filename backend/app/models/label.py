from app.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class LabelSchema(Base):
    """Esquema de etiquetas definido por proyecto."""
    __tablename__ = "label_schemas"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)   # ej: "nombre", "fecha", "lugar"
    color = Column(String(7), nullable=False, default="#3B82F6")  # hex color
    description = Column(String(255), nullable=True)
    shortcut = Column(String(10), nullable=True)  # atajo de teclado ej: "n", "f"
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="label_schemas")
    word_labels = relationship("WordLabel", back_populates="label_schema", cascade="all, delete-orphan")


class WordLabel(Base):
    """Relación muchos-a-muchos entre palabras y etiquetas."""
    __tablename__ = "word_labels"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    label_schema_id = Column(Integer, ForeignKey("label_schemas.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    word = relationship("Word", back_populates="word_labels")
    label_schema = relationship("LabelSchema", back_populates="word_labels")
