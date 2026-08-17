"""
Exporta pares (imagen, mascara de regiones) a partir de los LayoutRegion ya
etiquetados a mano en el proyecto, para entrenar el segmentador one-shot de
layout en Colab (ver colab/entrenar_segmentador_layout.ipynb).

Solo dos clases se modelan (ademas de fondo), siguiendo el alcance acordado:
    1 = Texto principal
    2 = Nota al margen
Firma, Sello/Timbre, Encabezado, Inscripcion extra y Decoracion se dejan como
fondo (0) en esta mascara -- siguen etiquetandose a mano, no las cubre este
modelo.

Uso:
    cd backend
    python -m scripts.export_layout_masks --project-id 1 --out ../colab/dataset_layout
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image, ImageDraw

from app.database import SessionLocal
from app.models.document import Document
from app.models.layout import LayoutRegion, LayoutRegionType


CLASS_IDS = {
    "Texto principal": 1,
    "Nota al margen": 2,
}
PREVIEW_COLORS = {
    0: (0, 0, 0),
    1: (59, 130, 246),   # azul -- mismo color que "Texto principal" en la app
    2: (245, 158, 11),   # naranja -- mismo color que "Nota al margen" en la app
}


def _colorize(mask: Image.Image) -> Image.Image:
    """Convierte la mascara de clases (0/1/2) en una imagen RGB legible para verificar a ojo."""
    arr = np.array(mask)
    lut = np.array([PREVIEW_COLORS[0], PREVIEW_COLORS[1], PREVIEW_COLORS[2]], dtype=np.uint8)
    rgb = lut[arr]
    return Image.fromarray(rgb, mode="RGB")


def export(project_id: int, out_dir: str) -> None:
    images_dir = os.path.join(out_dir, "images")
    masks_dir = os.path.join(out_dir, "masks")
    preview_dir = os.path.join(out_dir, "masks_preview")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(masks_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)

    db = SessionLocal()
    try:
        type_names = {t.id: t.name for t in db.query(LayoutRegionType).all()}

        query = db.query(Document)
        if project_id:
            query = query.filter(Document.project_id == project_id)
        documents = query.all()

        exported = 0
        for doc in documents:
            regions = db.query(LayoutRegion).filter(LayoutRegion.document_id == doc.id).all()
            if not regions:
                continue
            if not os.path.exists(doc.file_path):
                print(f"[omitido] Document {doc.id}: no existe {doc.file_path}")
                continue

            img = Image.open(doc.file_path).convert("RGB")
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)

            n_drawn = 0
            for r in regions:
                type_name = type_names.get(r.region_type_id)
                class_id = CLASS_IDS.get(type_name)
                if class_id is None:
                    continue
                x0, y0 = r.bbox_x, r.bbox_y
                x1, y1 = x0 + r.bbox_width, y0 + r.bbox_height
                draw.rectangle([x0, y0, x1, y1], fill=class_id)
                n_drawn += 1

            img.save(os.path.join(images_dir, f"{doc.id}.png"))
            mask.save(os.path.join(masks_dir, f"{doc.id}.png"))
            _colorize(mask).save(os.path.join(preview_dir, f"{doc.id}.png"))

            exported += 1
            print(f"[ok] Document {doc.id} ({doc.original_filename}) — {n_drawn} regiones (texto principal / nota al margen)")

        print(f"\nExportados {exported} pares imagen/mascara a {out_dir}")
        if exported < 3:
            print(
                "Aviso: con <3 paginas etiquetadas el entrenamiento one-shot puede no "
                "generalizar bien (ver research/segmentacion-layout-one-shot-manuscritos-arabes.md)."
            )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=None, help="Filtra por proyecto (opcional)")
    parser.add_argument("--out", type=str, default="../colab/dataset_layout", help="Directorio de salida")
    args = parser.parse_args()
    export(args.project_id, args.out)