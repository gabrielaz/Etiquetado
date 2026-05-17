from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os

from app.database import get_db
from app.models import Project, Document, Word, WordLabel
from app.schemas.document import DocumentOut, DocumentStatusUpdate
from app.services.image_service import save_uploaded_image, delete_image_file

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documentos"])


def _get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


def _enrich_document(doc: Document, db: Session) -> DocumentOut:
    word_count = db.query(func.count(Word.id)).filter(Word.document_id == doc.id).scalar()
    labeled_count = (
        db.query(func.count(func.distinct(WordLabel.word_id)))
        .join(Word, Word.id == WordLabel.word_id)
        .filter(Word.document_id == doc.id)
        .scalar()
    )
    out = DocumentOut.model_validate(doc)
    out.word_count = word_count
    out.labeled_count = labeled_count
    return out


@router.get("/", response_model=List[DocumentOut])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    _get_project_or_404(project_id, db)
    docs = db.query(Document).filter(Document.project_id == project_id).order_by(Document.created_at).all()
    return [_enrich_document(d, db) for d in docs]


@router.post("/", response_model=DocumentOut, status_code=201)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    _get_project_or_404(project_id, db)
    meta = await save_uploaded_image(file, project_id)
    doc = Document(project_id=project_id, **meta)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _enrich_document(doc, db)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(project_id: int, document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return _enrich_document(doc, db)


@router.get("/{document_id}/image")
def get_document_image(project_id: int, document_id: int, db: Session = Depends(get_db)):
    """Sirve la imagen original del documento."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")
    return FileResponse(
        doc.file_path,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.patch("/{document_id}/status", response_model=DocumentOut)
def update_document_status(
    project_id: int,
    document_id: int,
    payload: DocumentStatusUpdate,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    doc.status = payload.status
    db.commit()
    db.refresh(doc)
    return _enrich_document(doc, db)


@router.delete("/{document_id}", status_code=204)
def delete_document(project_id: int, document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    delete_image_file(doc.file_path)
    db.delete(doc)
    db.commit()
