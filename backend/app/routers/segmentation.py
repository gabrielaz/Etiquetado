"""
Router de segmentación asistida.

POST /documents/{document_id}/segment
  - Analiza la imagen con OpenCV
  - Devuelve bounding boxes sugeridos (sin persistir)

POST /documents/{document_id}/segment/apply
  - Analiza la imagen y persiste las palabras detectadas en la BD
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Document, Word
from app.schemas.word import SegmentationResult, SegmentedWord, BBox, WordOut, WordBulkCreate, WordCreate
from app.services.segmentation_service import run_segmentation

router = APIRouter(prefix="/documents/{document_id}", tags=["Segmentación Asistida"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.post("/segment", response_model=SegmentationResult)
def preview_segmentation(
    document_id: int,
    method: str = Query(default="contour", enum=["contour", "projection", "mser"]),
    db: Session = Depends(get_db)
):
    """
    Previsualiza la segmentación asistida SIN guardar en la base de datos.
    El frontend puede mostrar los bounding boxes sugeridos para revisión.

    Métodos disponibles:
    - **contour**: detección de contornos morfológicos (recomendado para la mayoría de manuscritos)
    - **projection**: proyección horizontal/vertical (mejor para documentos con líneas regulares)
    - **mser**: regiones estables maximalmente estables (para texto denso o fondos complejos)
    """
    doc = _get_document_or_404(document_id, db)

    try:
        raw_words = run_segmentation(doc.file_path, method=method)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en segmentación: {str(e)}")

    segmented = [
        SegmentedWord(
            bbox=BBox(
                x=w["x"], y=w["y"],
                width=w["width"], height=w["height"]
            ),
            confidence=w["confidence"],
            order_index=w["order_index"],
        )
        for w in raw_words
    ]

    return SegmentationResult(
        document_id=document_id,
        total_words=len(segmented),
        words=segmented,
        method=method,
    )


@router.post("/segment/apply", response_model=List[WordOut])
def apply_segmentation(
    document_id: int,
    method: str = Query(default="contour", enum=["contour", "projection", "mser"]),
    db: Session = Depends(get_db)
):
    """
    Ejecuta la segmentación y GUARDA las palabras detectadas en la base de datos.
    Las palabras anteriores con source='auto' son reemplazadas.
    Las palabras creadas manualmente (source='manual') se conservan.
    """
    doc = _get_document_or_404(document_id, db)

    try:
        raw_words = run_segmentation(doc.file_path, method=method)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en segmentación: {str(e)}")

    # Eliminar palabras auto anteriores
    db.query(Word).filter(
        Word.document_id == document_id,
        Word.source == "auto"
    ).delete()

    saved = []
    for w in raw_words:
        word = Word(
            document_id=document_id,
            bbox_x=float(w["x"]),
            bbox_y=float(w["y"]),
            bbox_width=float(w["width"]),
            bbox_height=float(w["height"]),
            confidence=w["confidence"],
            order_index=w["order_index"],
            source="auto",
        )
        db.add(word)
        saved.append(word)

    db.commit()
    for w in saved:
        db.refresh(w)

    # Construir respuesta simple (sin etiquetas aún)
    from app.schemas.word import WordOut
    return [WordOut.model_validate(w) for w in saved]
