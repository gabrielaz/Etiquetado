"""
Prueba el heuristico de segmentacion de layout (layout_segmentation_service)
contra las regiones ya marcadas a mano, para ver que tan cerca esta antes de
enchufarlo a un endpoint real.

Uso:
    cd backend
    python -m scripts.test_layout_segmentation --project-id 1
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.document import Document
from app.models.layout import LayoutRegion, LayoutRegionType
from app.models.word import Word
from app.services.layout_segmentation_service import segment_layout_regions


def test(project_id: int) -> None:
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.project_id == project_id).all()
        type_names = {t.id: t.name for t in db.query(LayoutRegionType).all()}

        for doc in documents:
            words = db.query(Word).filter(Word.document_id == doc.id).all()
            word_dicts = [
                {"x": w.bbox_x, "y": w.bbox_y, "width": w.bbox_width, "height": w.bbox_height}
                for w in words
                if None not in (w.bbox_x, w.bbox_y, w.bbox_width, w.bbox_height)
            ]
            if not word_dicts or not doc.image_width:
                continue

            predicted = segment_layout_regions(word_dicts, doc.image_width)
            actual = db.query(LayoutRegion).filter(LayoutRegion.document_id == doc.id).all()

            print(f"\n=== Documento {doc.id} ({doc.original_filename}) ===")
            print(f"-- Predicho por el heuristico ({len(predicted)} regiones) --")
            for p in predicted:
                print(f"  {p['region_type']:16s} x={p['x']:5d} y={p['y']:5d} w={p['width']:5d} h={p['height']:5d}  ({p['n_words']} palabras)")

            print(f"-- Marcado a mano ({len(actual)} regiones) --")
            for r in actual:
                name = type_names.get(r.region_type_id, "?")
                print(f"  {name:16s} x={r.bbox_x:5.0f} y={r.bbox_y:5.0f} w={r.bbox_width:5.0f} h={r.bbox_height:5.0f}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=1)
    args = parser.parse_args()
    test(args.project_id)