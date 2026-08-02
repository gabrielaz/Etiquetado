from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.project import Project
from app.models.document import Document
from app.models.layout import LayoutRegionType, LayoutRegion
from app.schemas.layout import (
    LayoutRegionTypeCreate, LayoutRegionTypeUpdate, LayoutRegionTypeOut,
    LayoutRegionCreate, LayoutRegionUpdate, LayoutRegionOut,
    SegmentedLayoutRegion, LayoutRegionSegmentationResult,
)
from app.schemas.word import BBox
from app.services.layout_ml_service import segment_by_ml

# ─── Tipos de región (por proyecto) ──────────────────────────────────────────
types_router = APIRouter(prefix="/projects/{project_id}/layout-region-types", tags=["DLA - Tipos de Región"])

DLA_DEFAULTS = [
    {"name": "Texto principal",    "color": "#3B82F6", "shortcut": "t"},
    {"name": "Nota al margen",     "color": "#F59E0B", "shortcut": "n"},
    {"name": "Firma",              "color": "#10B981", "shortcut": "f"},
    {"name": "Sello / Timbre",     "color": "#8B5CF6", "shortcut": "s"},
    {"name": "Encabezado",         "color": "#EF4444", "shortcut": "e"},
    {"name": "Inscripción extra",  "color": "#EC4899", "shortcut": "i"},
    {"name": "Decoración",         "color": "#6B7280", "shortcut": "d"},
]


@types_router.get("/", response_model=List[LayoutRegionTypeOut])
def list_region_types(project_id: int, db: Session = Depends(get_db)):
    _get_project_or_404(project_id, db)
    return db.query(LayoutRegionType).filter(LayoutRegionType.project_id == project_id).all()


@types_router.post("/", response_model=LayoutRegionTypeOut, status_code=201)
def create_region_type(project_id: int, payload: LayoutRegionTypeCreate, db: Session = Depends(get_db)):
    _get_project_or_404(project_id, db)
    rt = LayoutRegionType(project_id=project_id, **payload.model_dump())
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


@types_router.post("/seed-defaults", response_model=List[LayoutRegionTypeOut], status_code=201)
def seed_default_types(project_id: int, db: Session = Depends(get_db)):
    """Crea los tipos de región predefinidos para un proyecto."""
    _get_project_or_404(project_id, db)
    existing = {r.name for r in db.query(LayoutRegionType).filter(LayoutRegionType.project_id == project_id).all()}
    created = []
    for d in DLA_DEFAULTS:
        if d["name"] not in existing:
            rt = LayoutRegionType(project_id=project_id, **d)
            db.add(rt)
            created.append(rt)
    db.commit()
    for r in created:
        db.refresh(r)
    return created


@types_router.patch("/{type_id}", response_model=LayoutRegionTypeOut)
def update_region_type(project_id: int, type_id: int, payload: LayoutRegionTypeUpdate, db: Session = Depends(get_db)):
    rt = db.query(LayoutRegionType).filter(
        LayoutRegionType.id == type_id,
        LayoutRegionType.project_id == project_id
    ).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Tipo de región no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rt, field, value)
    db.commit()
    db.refresh(rt)
    return rt


@types_router.delete("/{type_id}", status_code=204)
def delete_region_type(project_id: int, type_id: int, db: Session = Depends(get_db)):
    rt = db.query(LayoutRegionType).filter(
        LayoutRegionType.id == type_id,
        LayoutRegionType.project_id == project_id
    ).first()
    if not rt:
        raise HTTPException(status_code=404, detail="Tipo de región no encontrado")
    db.delete(rt)
    db.commit()


# ─── Regiones (por documento) ─────────────────────────────────────────────────
regions_router = APIRouter(prefix="/documents/{document_id}/layout-regions", tags=["DLA - Regiones"])


def _get_project_or_404(project_id: int, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return p


def _enrich(region: LayoutRegion, db: Session) -> LayoutRegionOut:
    rt = db.query(LayoutRegionType).filter(LayoutRegionType.id == region.region_type_id).first() if region.region_type_id else None
    out = LayoutRegionOut.model_validate(region)
    out.type_name = rt.name if rt else None
    out.type_color = rt.color if rt else None
    return out

def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@regions_router.post("/segment", response_model=LayoutRegionSegmentationResult)
def preview_layout_segmentation(document_id: int, db: Session = Depends(get_db)):
    """Previsualiza regiones DLA sugeridas por el modelo ML, sin guardar."""
    doc = _get_document_or_404(document_id, db)

    try:
        raw_regions = segment_by_ml(doc.file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en segmentación ML: {str(e)}")

    segmented = [
        SegmentedLayoutRegion(
            bbox=BBox(x=r["x"], y=r["y"], width=r["width"], height=r["height"]),
            region_type_name=r["region_type"],
            confidence=r["confidence"],
            order_index=r["order_index"],
        )
        for r in raw_regions
    ]
    return LayoutRegionSegmentationResult(
        document_id=document_id,
        total_regions=len(segmented),
        regions=segmented,
    )


@regions_router.post("/segment/apply", response_model=List[LayoutRegionOut])
def apply_layout_segmentation(document_id: int, db: Session = Depends(get_db)):
    """Ejecuta la segmentación ML y persiste las regiones. Reemplaza solo las
    regiones con source='auto' previas; conserva las dibujadas a mano."""
    doc = _get_document_or_404(document_id, db)

    try:
        raw_regions = segment_by_ml(doc.file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en segmentación ML: {str(e)}")

    type_by_name = {
        rt.name: rt.id
        for rt in db.query(LayoutRegionType).filter(LayoutRegionType.project_id == doc.project_id).all()
    }
    missing = {r["region_type"] for r in raw_regions} - set(type_by_name.keys())
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Faltan tipos de región en este proyecto: {', '.join(missing)}. Corré /seed-defaults primero."
        )

    db.query(LayoutRegion).filter(
        LayoutRegion.document_id == document_id,
        LayoutRegion.source == "auto"
    ).delete()

    saved = []
    for r in raw_regions:
        region = LayoutRegion(
            document_id=document_id,
            region_type_id=type_by_name[r["region_type"]],
            order_index=r["order_index"],
            bbox_x=float(r["x"]),
            bbox_y=float(r["y"]),
            bbox_width=float(r["width"]),
            bbox_height=float(r["height"]),
            source="auto",
        )
        db.add(region)
        saved.append(region)

    db.commit()
    for r in saved:
        db.refresh(r)

    return [_enrich(r, db) for r in saved]

@regions_router.get("/", response_model=List[LayoutRegionOut])
def list_regions(document_id: int, db: Session = Depends(get_db)):
    regions = db.query(LayoutRegion).filter(
        LayoutRegion.document_id == document_id
    ).order_by(LayoutRegion.order_index).all()
    return [_enrich(r, db) for r in regions]


@regions_router.post("/", response_model=LayoutRegionOut, status_code=201)
def create_region(document_id: int, payload: LayoutRegionCreate, db: Session = Depends(get_db)):
    region = LayoutRegion(document_id=document_id, **payload.model_dump())
    db.add(region)
    db.commit()
    db.refresh(region)
    return _enrich(region, db)


@regions_router.patch("/{region_id}", response_model=LayoutRegionOut)
def update_region(document_id: int, region_id: int, payload: LayoutRegionUpdate, db: Session = Depends(get_db)):
    region = db.query(LayoutRegion).filter(
        LayoutRegion.id == region_id,
        LayoutRegion.document_id == document_id
    ).first()
    if not region:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(region, field, value)
    db.commit()
    db.refresh(region)
    return _enrich(region, db)


@regions_router.delete("/{region_id}", status_code=204)
def delete_region(document_id: int, region_id: int, db: Session = Depends(get_db)):
    region = db.query(LayoutRegion).filter(
        LayoutRegion.id == region_id,
        LayoutRegion.document_id == document_id
    ).first()
    if not region:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    db.delete(region)
    db.commit()
