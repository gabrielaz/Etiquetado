"""
Servicio de segmentación asistida de palabras en documentos manuscritos.

Usa OpenCV para detectar automáticamente bounding boxes de palabras.
Estrategias disponibles:
  - 'contour'    : detección de contornos (buena para escritura aislada)
  - 'projection' : proyección horizontal/vertical (buena para líneas regulares)
  - 'mser'       : MSER (Maximally Stable Extremal Regions) para texto denso
"""

import cv2
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def _load_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"No se puede cargar la imagen: {image_path}")
    return img


def _preprocess(img: np.ndarray) -> np.ndarray:
    """Convierte a escala de grises, aplica desenfoque y umbral adaptativo."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Desenfoque para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Umbral adaptativo — mejor para variaciones de iluminación en manuscritos
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=10
    )
    return thresh


def _filter_bbox(x: int, y: int, w: int, h: int,
                 img_w: int, img_h: int,
                 min_area: int = 100,
                 min_aspect: float = 0.05,
                 max_aspect: float = 20.0) -> bool:
    """Filtra bounding boxes demasiado pequeños, grandes o con proporción inválida."""
    area = w * h
    if area < min_area:
        return False
    aspect = w / h if h > 0 else 0
    if aspect < min_aspect or aspect > max_aspect:
        return False
    # Descartar si es casi toda la imagen (ruido de fondo)
    if w > img_w * 0.9 or h > img_h * 0.9:
        return False
    return True


def _merge_nearby_boxes(boxes: List[Tuple[int, int, int, int]],
                        gap_x: int = 20,
                        gap_y: int = 10) -> List[Tuple[int, int, int, int]]:
    """
    Fusiona bounding boxes cercanos horizontalmente para agrupar letras en palabras.
    gap_x: distancia máxima horizontal para considerar misma palabra.
    gap_y: tolerancia vertical para estar en la misma línea.
    """
    if not boxes:
        return []

    # Ordenar por x
    boxes = sorted(boxes, key=lambda b: (b[1] // 30, b[0]))  # agrupar por línea aprox.
    merged = []
    current = list(boxes[0])

    for box in boxes[1:]:
        x, y, w, h = box
        cx, cy, cw, ch = current

        # Centro vertical similar (misma línea) y cerca horizontalmente
        same_line = abs((cy + ch // 2) - (y + h // 2)) < gap_y + ch * 0.5
        close_x = x <= cx + cw + gap_x

        if same_line and close_x:
            # Fusionar
            new_x = min(cx, x)
            new_y = min(cy, y)
            new_w = max(cx + cw, x + w) - new_x
            new_h = max(cy + ch, y + h) - new_y
            current = [new_x, new_y, new_w, new_h]
        else:
            merged.append(tuple(current))
            current = list(box)

    merged.append(tuple(current))
    return merged


def segment_by_contour(image_path: str,
                       merge_gap_x: int = 15,
                       merge_gap_y: int = 8) -> List[dict]:
    """
    Detecta palabras usando detección de contornos + fusión de boxes cercanos.

    Returns:
        Lista de dicts con: x, y, width, height, confidence, order_index
    """
    img = _load_image(image_path)
    img_h, img_w = img.shape[:2]
    thresh = _preprocess(img)

    # Apertura morfológica: elimina motas de tinta/ruido de papel antes de fusionar
    # letras, para que no se cuenten como palabras (ver calibración con GT real).
    denoise_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, denoise_kernel)

    # Operación morfológica para conectar letras de la misma palabra
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (merge_gap_x, 3))
    dilated = cv2.dilate(opened, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # min_area calibrado contra GT real (mediana ~36873px², p5 ~13143px²)
        # a 400 DPI — 100 (default) dejaba pasar manchas y motas de tinta.
        if _filter_bbox(x, y, w, h, img_w, img_h, min_area=5000):
            raw_boxes.append((x, y, w, h))

    # Ordenar de arriba a abajo, izquierda a derecha
    raw_boxes = sorted(raw_boxes, key=lambda b: (b[1] // 40, b[0]))

    results = []
    for idx, (x, y, w, h) in enumerate(raw_boxes):
        results.append({
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "confidence": 0.75,
            "order_index": idx,
        })

    logger.info(f"Segmentación por contorno: {len(results)} palabras detectadas en {image_path}")
    return results


def _segment_1d(proj: np.ndarray, threshold: float, min_gap: int, min_run: int) -> List[Tuple[int, int]]:
    """
    Agrupa un perfil de proyección 1D en segmentos [start, end) por encima del
    umbral, tolerando huecos cortos (< min_gap muestras) para no cortar por una
    plumada/rúbrica que cruza brevemente el hueco entre línea o palabra.
    Descarta segmentos más angostos que min_run.
    """
    segments: List[Tuple[int, int]] = []
    in_seg = False
    seg_start = 0
    gap_start = None

    for i, val in enumerate(proj):
        if val > threshold:
            if not in_seg:
                in_seg = True
                seg_start = i
            gap_start = None
        elif in_seg:
            if gap_start is None:
                gap_start = i
            if i - gap_start >= min_gap:
                if gap_start - seg_start >= min_run:
                    segments.append((seg_start, gap_start))
                in_seg = False
                gap_start = None

    if in_seg:
        end = gap_start if gap_start is not None else len(proj)
        if end - seg_start >= min_run:
            segments.append((seg_start, end))

    return segments


def segment_by_projection(image_path: str) -> List[dict]:
    """
    Detecta palabras usando proyección horizontal (line detection) y
    proyección vertical (word separation within a line).

    Más robusto para documentos con líneas horizontales regulares.
    """
    img = _load_image(image_path)
    img_h, img_w = img.shape[:2]
    thresh = _preprocess(img)

    # --- Paso 1: Detectar líneas de texto via proyección horizontal ---
    # min_gap=6: tolera que una plumada/rúbrica cruce brevemente el hueco entre
    # líneas sin fusionarlas; sin esto, la cursiva conectada agrupaba párrafos
    # enteros en una sola "línea" (calibrado contra GT real).
    h_proj = np.sum(thresh, axis=1)  # suma de píxeles por fila
    threshold_h = np.max(h_proj) * 0.08
    lines = _segment_1d(h_proj, threshold_h, min_gap=6, min_run=5)

    results = []
    word_idx = 0

    # --- Paso 2: Por cada línea, proyección vertical para separar palabras ---
    for (row_start, row_end) in lines:
        line_strip = thresh[row_start:row_end, :]
        v_proj = np.sum(line_strip, axis=0)
        threshold_v = np.max(v_proj) * 0.05 if np.max(v_proj) > 0 else 1
        # min_gap=10: hueco real entre palabras (p25 ~17.6px en la GT) — antes
        # se cortaba palabra apenas la proyección caía por una sola columna.
        words = _segment_1d(v_proj, threshold_v, min_gap=10, min_run=1)

        for (col_start, col_end) in words:
            w = col_end - col_start
            h = row_end - row_start
            if _filter_bbox(col_start, row_start, w, h, img_w, img_h, min_area=50):
                results.append({
                    "x": int(col_start),
                    "y": int(row_start),
                    "width": int(w),
                    "height": int(h),
                    "confidence": 0.65,
                    "order_index": word_idx,
                })
                word_idx += 1

    logger.info(f"Segmentación por proyección: {len(results)} palabras detectadas en {image_path}")
    return results


def segment_by_mser(image_path: str) -> List[dict]:
    """
    Usa MSER (Maximally Stable Extremal Regions) para detectar regiones de texto.
    Útil para documentos con escritura densa o fondos complejos.
    """
    img = _load_image(image_path)
    img_h, img_w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    mser = cv2.MSER_create(
        delta=5,
        min_area=60,
        # 0.0035 en vez de 0.01: contra la GT real, 1% de esta imagen (~336k px²)
        # superaba hasta la palabra más grande observada (293k px²) — el filtro
        # no rechazaba ni líneas completas fusionadas.
        max_area=int(img_w * img_h * 0.0035),
    )
    regions, _ = mser.detectRegions(gray)

    raw_boxes = []
    for region in regions:
        x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
        # max_aspect=9: una "línea larga" fusionada es justamente una caja de
        # aspecto extremo que el default (20) dejaba pasar.
        if _filter_bbox(x, y, w, h, img_w, img_h, max_aspect=9.0):
            raw_boxes.append((x, y, w, h))

    # Fusionar boxes cercanos para agrupar en palabras
    # gap_x=12 (antes 18): por debajo del hueco real p25 entre palabras (~17.6px)
    # para no fusionar palabras distintas.
    merged = _merge_nearby_boxes(raw_boxes, gap_x=12, gap_y=12)
    merged = sorted(merged, key=lambda b: (b[1] // 40, b[0]))

    results = []
    for idx, (x, y, w, h) in enumerate(merged):
        results.append({
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "confidence": 0.70,
            "order_index": idx,
        })

    logger.info(f"Segmentación MSER: {len(results)} palabras detectadas en {image_path}")
    return results


def run_segmentation(image_path: str, method: str = "contour") -> List[dict]:
    """
    Punto de entrada principal del servicio de segmentación.

    Args:
        image_path: ruta absoluta a la imagen
        method: 'contour' | 'projection' | 'mser'

    Returns:
        Lista de palabras segmentadas con bbox y metadatos
    """
    methods = {
        "contour": segment_by_contour,
        "projection": segment_by_projection,
        "mser": segment_by_mser,
    }
    if method not in methods:
        raise ValueError(f"Método desconocido: {method}. Use: {list(methods.keys())}")

    return methods[method](image_path)
