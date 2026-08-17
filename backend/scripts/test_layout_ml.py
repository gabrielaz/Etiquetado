"""
Prueba el modelo ML de segmentacion de layout (layout_ml_service) contra las
regiones marcadas a mano, mismo patron que test_layout_segmentation.py (para
comparar el enfoque geometrico vs. el ML).

Uso:
    cd backend
    python -m scripts.test_layout_ml --project-id 1
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.document import Document
from app.models.layout import LayoutRegion, LayoutRegionType
from app.services.layout_ml_service import segment_by_ml


def test(project_id: int) -> None:
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.project_id == project_id).all()
        type_names = {t.id: t.name for t in db.query(LayoutRegionType).all()}

        for doc in documents:
            if not os.path.exists(doc.file_path):
                continue

            predicted = segment_by_ml(doc.file_path)
            actual = db.query(LayoutRegion).filter(LayoutRegion.document_id == doc.id).all()

            print(f"\n=== Documento {doc.id} ({doc.original_filename}) ===")
            print(f"-- Predicho por el modelo ML ({len(predicted)} regiones) --")
            for p in predicted:
                print(f"  {p['region_type']:16s} x={p['x']:5d} y={p['y']:5d} w={p['width']:5d} h={p['height']:5d}")

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