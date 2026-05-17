from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Document, Word, WordLabel, LabelSchema
from app.schemas.word import WordCreate, WordUpdate, WordOut, WordBulkCreate, WordLabelOut
from app.schemas.label import WordLabelCreate

router = APIRouter(prefix="/documents/{document_id}/words", tags=["Palabras"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


def _word_to_out(word: Word, db: Session) -> WordOut:
    labels = db.query(WordLabel).filter(WordLabel.word_id == word.id).all()
    label_outs = []
    for wl in labels:
        schema = db.query(LabelSchema).filter(LabelSchema.id == wl.label_schema_id).first()
        label_outs.append(WordLabelOut(
            id=wl.id,
            label_schema_id=wl.label_schema_id,
            label_name=schema.name if schema else None,
            label_color=schema.color if schema else None,
        ))
    out = WordOut.model_validate(word)
    out.labels = label_outs
    return out


@router.get("/", response_model=List[WordOut])
def list_words(document_id: int, db: Session = Depends(get_db)):
    _get_document_or_404(document_id, db)
    words = db.query(Word).filter(Word.document_id == document_id).order_by(Word.order_index).all()
    return [_word_to_out(w, db) for w in words]


@router.post("/", response_model=WordOut, status_code=201)
def create_word(document_id: int, payload: WordCreate, db: Session = Depends(get_db)):
    _get_document_or_404(document_id, db)
    word = Word(document_id=document_id, **payload.model_dump())
    db.add(word)
    db.commit()
    db.refresh(word)
    return _word_to_out(word, db)


@router.post("/bulk", response_model=List[WordOut], status_code=201)
def bulk_create_words(document_id: int, payload: WordBulkCreate, db: Session = Depends(get_db)):
    """Importar múltiples palabras de una vez (desde segmentación asistida)."""
    _get_document_or_404(document_id, db)

    # Eliminar palabras automáticas existentes para evitar duplicados
    db.query(Word).filter(
        Word.document_id == document_id,
        Word.source == "auto"
    ).delete()

    words = []
    for w_data in payload.words:
        word = Word(document_id=document_id, **w_data.model_dump())
        db.add(word)
        words.append(word)

    db.commit()
    for w in words:
        db.refresh(w)
    return [_word_to_out(w, db) for w in words]


@router.get("/{word_id}", response_model=WordOut)
def get_word(document_id: int, word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id, Word.document_id == document_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    return _word_to_out(word, db)


@router.patch("/{word_id}", response_model=WordOut)
def update_word(document_id: int, word_id: int, payload: WordUpdate, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id, Word.document_id == document_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(word, field, value)
    db.commit()
    db.refresh(word)
    return _word_to_out(word, db)


@router.delete("/{word_id}", status_code=204)
def delete_word(document_id: int, word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id, Word.document_id == document_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    db.delete(word)
    db.commit()


# --- Etiquetas de una palabra ---

@router.post("/{word_id}/labels", status_code=201)
def assign_label(
    document_id: int,
    word_id: int,
    payload: WordLabelCreate,
    db: Session = Depends(get_db)
):
    word = db.query(Word).filter(Word.id == word_id, Word.document_id == document_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")

    schema = db.query(LabelSchema).filter(LabelSchema.id == payload.label_schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

    # Evitar duplicados
    existing = db.query(WordLabel).filter(
        WordLabel.word_id == word_id,
        WordLabel.label_schema_id == payload.label_schema_id
    ).first()
    if existing:
        return {"message": "Etiqueta ya asignada"}

    wl = WordLabel(word_id=word_id, label_schema_id=payload.label_schema_id)
    db.add(wl)
    db.commit()
    return {"message": "Etiqueta asignada", "word_label_id": wl.id}


@router.delete("/{word_id}/labels/{label_schema_id}", status_code=204)
def remove_label(
    document_id: int,
    word_id: int,
    label_schema_id: int,
    db: Session = Depends(get_db)
):
    wl = db.query(WordLabel).filter(
        WordLabel.word_id == word_id,
        WordLabel.label_schema_id == label_schema_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Asignación de etiqueta no encontrada")
    db.delete(wl)
    db.commit()
