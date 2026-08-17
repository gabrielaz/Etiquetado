"""
Exporta pares (imagen, máscara binaria de palabras) a partir de los Documents ya
etiquetados en el proyecto, para entrenar/afinar un segmentador de palabras en Colab
(ver colab/entrenar_segmentador_palabras.ipynb).

Uso:
    cd backend
    python -m scripts.export_word_masks --project-id 1 --out ../colab/dataset

Para cada Document con al menos 1 Word (source=manual o auto), genera:
    dataset/images/<document_id>.png   — imagen original
    dataset/masks/<document_id>.png    — máscara 1 canal: 255 = palabra, 0 = fondo,
                                          rasterizada a partir de los bbox de Word

No requiere ningún cambio en la app en ejecución: es un script offline de una sola vez.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image, ImageDraw

from app.database import SessionLocal
from app.models.document import Document
from app.models.word import Word


def export(project_id: int, out_dir: str) -> None:
    images_dir = os.path.join(out_dir, "images")
    masks_dir = os.path.join(out_dir, "masks")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(masks_dir, exist_ok=True)

    db = SessionLocal()
    try:
        query = db.query(Document)
        if project_id:
            query = query.filter(Document.project_id == project_id)
        documents = query.all()

        exported = 0
        for doc in documents:
            words = db.query(Word).filter(Word.document_id == doc.id).all()
            words = [w for w in words if None not in (w.bbox_x, w.bbox_y, w.bbox_width, w.bbox_height)]
            if not words:
                continue
            if not os.path.exists(doc.file_path):
                print(f"[omitido] Document {doc.id}: no existe {doc.file_path}")
                continue

            img = Image.open(doc.file_path).convert("RGB")
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            for w in words:
                x0, y0 = w.bbox_x, w.bbox_y
                x1, y1 = x0 + w.bbox_width, y0 + w.bbox_height
                draw.rectangle([x0, y0, x1, y1], fill=255)

            img.save(os.path.join(images_dir, f"{doc.id}.png"))
            mask.save(os.path.join(masks_dir, f"{doc.id}.png"))
            exported += 1
            print(f"[ok] Document {doc.id} ({doc.original_filename}) — {len(words)} palabras")

        print(f"\nExportados {exported} pares imagen/máscara a {out_dir}")
        if exported < 3:
            print(
                "Aviso: con <3 páginas etiquetadas el entrenamiento en modo one-shot/few-shot "
                "(ver research/segmentacion-layout-one-shot-manuscritos-arabes.md) puede no "
                "generalizar bien. Etiqueta manualmente 1-3 páginas representativas del corpus "
                "antes de exportar si aún no lo hiciste."
            )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=None, help="Filtra por proyecto (opcional)")
    parser.add_argument("--out", type=str, default="../colab/dataset", help="Directorio de salida")
    args = parser.parse_args()
    export(args.project_id, args.out)
