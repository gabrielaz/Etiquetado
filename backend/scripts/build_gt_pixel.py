"""
Construye ground truth *pixel-precise* a partir de las LayoutRegion rectangulares
etiquetadas en la app, para poder comparar contra las metricas del paper
De Nardin et al. (WACV 2024) -- ver issue #1.

Por que hace falta:
    export_layout_masks.py exporta la mascara como rectangulos planos: todo pixel
    dentro del bbox queda marcado como "Texto principal" o "Nota al margen",
    incluido el papel en blanco entre renglones. El GT del paper, en cambio, es
    pixel-precise: solo los pixeles de *tinta* pertenecen a una clase. Comparar
    un F1 calculado sobre rectangulos contra el F1 del paper no significa nada,
    porque no miden lo mismo.

    Este script cierra esa brecha intersectando los rectangulos anotados con la
    mascara de tinta obtenida por umbralizacion de Sauvola -- la misma operacion
    (y los mismos hiperparametros, ventana 31, k=0.2) que el paper aplica a sus
    *predicciones* en la etapa de refinamiento, aplicada aca al GT.

Uso:
    cd backend
    python -m scripts.build_gt_pixel --project-id 2 --out ../colab/dataset_layout_arabe
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image, ImageDraw
from skimage.color import rgb2gray
from skimage.filters import threshold_sauvola

from app.database import SessionLocal
from app.models.document import Document
from app.models.layout import LayoutRegion, LayoutRegionType

from scripts.export_layout_masks import CLASS_IDS, _colorize

# Mismos valores que el paper (seccion 4.3) y que refine_with_sauvola() en el notebook.
SAUVOLA_WINDOW = 31
SAUVOLA_K = 0.2


def ink_mask(img_rgb: np.ndarray, window_size: int = SAUVOLA_WINDOW, k: float = SAUVOLA_K) -> np.ndarray:
    """Binariza la pagina con Sauvola. True = pixel de tinta, False = soporte/papel."""
    gray = rgb2gray(img_rgb)
    thresh = threshold_sauvola(gray, window_size=window_size, k=k)
    return gray < thresh


def rasterize_regions(regions, type_names, size) -> np.ndarray:
    """
    Rasteriza los bboxes anotados a un mapa de clases (0 fondo / 1 principal / 2 marginal).

    Regla de solape explicita: "Nota al margen" se dibuja *despues* de "Texto principal",
    asi que gana en las zonas donde ambos rectangulos se pisan. Es necesario porque
    LayoutRegion solo guarda bbox alineado a los ejes (backend/app/models/layout.py:22) y
    la marginalia arabe corre en diagonal, de modo que su rectangulo envolvente invade el
    bloque central. Sin esta regla la marginalia quedaria borrada por el texto principal.
    """
    canvas = Image.new("L", size, 0)
    draw = ImageDraw.Draw(canvas)

    por_clase = {1: [], 2: []}
    for r in regions:
        class_id = CLASS_IDS.get(type_names.get(r.region_type_id))
        if class_id is not None:
            por_clase[class_id].append(r)

    for class_id in (1, 2):  # el orden importa: 2 pisa a 1
        for r in por_clase[class_id]:
            x0, y0 = r.bbox_x, r.bbox_y
            draw.rectangle([x0, y0, x0 + r.bbox_width, y0 + r.bbox_height], fill=class_id)

    return np.array(canvas, dtype=np.uint8)


def build_pixel_gt(img_rgb: np.ndarray, class_map: np.ndarray) -> np.ndarray:
    """
    Combina el mapa de clases rectangular con la mascara de tinta para producir el GT
    pixel-precise.

    Entradas:
        img_rgb   -- (H, W, 3) uint8, la pagina original.
        class_map -- (H, W) uint8 con 0/1/2, salida de rasterize_regions().

    Salida:
        (H, W) uint8 con 0/1/2, donde un pixel vale 1 o 2 solo si ademas es tinta.
        Todo lo que sea papel dentro de un rectangulo vuelve a 0.
    """
    return np.where(ink_mask(img_rgb), class_map, 0).astype(np.uint8)


def export(project_id: int, out_dir: str) -> None:
    images_dir = os.path.join(out_dir, "images")
    masks_dir = os.path.join(out_dir, "masks")
    preview_dir = os.path.join(out_dir, "masks_preview")
    for d in (images_dir, masks_dir, preview_dir):
        os.makedirs(d, exist_ok=True)

    db = SessionLocal()
    try:
        type_names = {t.id: t.name for t in db.query(LayoutRegionType).all()}

        query = db.query(Document)
        if project_id:
            query = query.filter(Document.project_id == project_id)

        exported = 0
        for doc in query.all():
            regions = db.query(LayoutRegion).filter(LayoutRegion.document_id == doc.id).all()
            if not regions:
                continue
            if not os.path.exists(doc.file_path):
                print(f"[omitido] Document {doc.id}: no existe {doc.file_path}")
                continue

            img = Image.open(doc.file_path).convert("RGB")
            img_rgb = np.array(img)

            class_map = rasterize_regions(regions, type_names, img.size)
            gt = build_pixel_gt(img_rgb, class_map)

            img.save(os.path.join(images_dir, f"{doc.id}.png"))
            Image.fromarray(gt, mode="L").save(os.path.join(masks_dir, f"{doc.id}.png"))
            _colorize(Image.fromarray(gt, mode="L")).save(os.path.join(preview_dir, f"{doc.id}.png"))

            cobertura = {c: float((gt == c).mean()) for c in (1, 2)}
            print(
                f"[ok] Document {doc.id} ({doc.original_filename}) — "
                f"principal {cobertura[1]:.2%} / marginal {cobertura[2]:.2%} de la pagina"
            )
            exported += 1

        print(f"\nExportados {exported} pares imagen/mascara pixel-precise a {out_dir}")
        print("Revisa masks_preview/ a ojo antes de entrenar: si el GT esta mal, las metricas no significan nada.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=None, help="Filtra por proyecto")
    parser.add_argument("--out", type=str, default="../colab/dataset_layout_arabe", help="Directorio de salida")
    args = parser.parse_args()
    export(args.project_id, args.out)
