"""
Analiza las regiones de layout ya etiquetadas a mano (LayoutRegion) para sacar
estadisticas geometricas reales por tipo (Texto principal, Nota al margen, etc.)
y asi calibrar el detector heuristico en vez de adivinar umbrales, igual que se
hizo con las palabras en segmentation_service.py.

Uso:
    cd backend
    python -m scripts.analyze_layout_gt --project-id 1
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import defaultdict

from app.database import SessionLocal
from app.models.document import Document
from app.models.layout import LayoutRegion, LayoutRegionType
from app.models.word import Word


def bbox_contains_center(region: LayoutRegion, word: Word) -> bool:
    cx = word.bbox_x + word.bbox_width / 2
    cy = word.bbox_y + word.bbox_height / 2
    return (
        region.bbox_x <= cx <= region.bbox_x + region.bbox_width
        and region.bbox_y <= cy <= region.bbox_y + region.bbox_height
    )


def analyze(project_id: int) -> None:
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.project_id == project_id).all()
        doc_by_id = {d.id: d for d in documents}
        doc_ids = list(doc_by_id.keys())
        if not doc_ids:
            print(f"No hay documentos en el proyecto {project_id}")
            return

        regions = db.query(LayoutRegion).filter(LayoutRegion.document_id.in_(doc_ids)).all()
        if not regions:
            print("No hay layout_regions etiquetadas todavia")
            return

        words_by_doc = defaultdict(list)
        for w in db.query(Word).filter(Word.document_id.in_(doc_ids)).all():
            if None not in (w.bbox_x, w.bbox_y, w.bbox_width, w.bbox_height):
                words_by_doc[w.document_id].append(w)

        type_names = {t.id: t.name for t in db.query(LayoutRegionType).all()}

        stats = defaultdict(list)
        for r in regions:
            doc = doc_by_id[r.document_id]
            if not doc.image_width or not doc.image_height:
                continue
            type_name = type_names.get(r.region_type_id, "(sin tipo)")

            width_ratio = r.bbox_width / doc.image_width
            left_ratio = r.bbox_x / doc.image_width
            right_ratio = (r.bbox_x + r.bbox_width) / doc.image_width
            aspect = r.bbox_width / r.bbox_height
            area = r.bbox_width * r.bbox_height

            n_words = sum(1 for w in words_by_doc[r.document_id] if bbox_contains_center(r, w))
            density = n_words / (area / 1_000_000)

            stats[type_name].append({
                "width_ratio": width_ratio,
                "left_ratio": left_ratio,
                "right_ratio": right_ratio,
                "aspect": aspect,
                "n_words": n_words,
                "density": density,
            })

        print(f"\n=== Estadisticas de layout_regions - proyecto {project_id} ===\n")
        for type_name, rows in sorted(stats.items()):
            print(f"--- {type_name} ({len(rows)} regiones) ---")
            for key in ("width_ratio", "left_ratio", "right_ratio", "aspect", "density"):
                values = [row[key] for row in rows]
                avg = sum(values) / len(values)
                print(f"  {key:12s}  avg={avg:6.2f}  min={min(values):6.2f}  max={max(values):6.2f}")
            print(f"  n_words por region: {[row['n_words'] for row in rows]}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=1, help="Proyecto a analizar")
    args = parser.parse_args()
    analyze(args.project_id)