from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Project, LabelSchema
from app.schemas.label import LabelSchemaCreate, LabelSchemaUpdate, LabelSchemaOut

router = APIRouter(prefix="/projects/{project_id}/labels", tags=["Esquemas de Etiquetas"])

# Paleta de colores por defecto para nuevas etiquetas
DEFAULT_COLORS = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B",
    "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
]


@router.get("/", response_model=List[LabelSchemaOut])
def list_labels(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return db.query(LabelSchema).filter(LabelSchema.project_id == project_id).all()


@router.post("/", response_model=LabelSchemaOut, status_code=201)
def create_label(project_id: int, payload: LabelSchemaCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Asignar color automático si no se especifica
    existing_count = db.query(LabelSchema).filter(LabelSchema.project_id == project_id).count()
    if not payload.color or payload.color == "#3B82F6":
        color = DEFAULT_COLORS[existing_count % len(DEFAULT_COLORS)]
    else:
        color = payload.color

    data = payload.model_dump()
    data["color"] = color
    label = LabelSchema(project_id=project_id, **data)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


@router.patch("/{label_id}", response_model=LabelSchemaOut)
def update_label(
    project_id: int,
    label_id: int,
    payload: LabelSchemaUpdate,
    db: Session = Depends(get_db)
):
    label = db.query(LabelSchema).filter(
        LabelSchema.id == label_id,
        LabelSchema.project_id == project_id
    ).first()
    if not label:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(label, field, value)
    db.commit()
    db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=204)
def delete_label(project_id: int, label_id: int, db: Session = Depends(get_db)):
    label = db.query(LabelSchema).filter(
        LabelSchema.id == label_id,
        LabelSchema.project_id == project_id
    ).first()
    if not label:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    db.delete(label)
    db.commit()
