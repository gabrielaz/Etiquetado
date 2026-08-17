"""
Servicio de inferencia ML para segmentacion de layout (texto principal / nota al
margen), usando el modelo entrenado en colab/entrenar_segmentador_layout.ipynb
(DeepLabv3+ + Dynamic Instance Generation + refinamiento Sauvola, ver
research/segmentacion-layout-one-shot-manuscritos-arabes.md en el vault).

Carga backend/app/ml/layout_segmenter.onnx una sola vez (sesion global) y expone
segment_by_ml(image_path), con el mismo formato de salida que
layout_segmentation_service.segment_layout_regions.
"""

import os
from typing import List, Tuple

import cv2
import numpy as np
import onnxruntime as ort
from skimage.color import rgb2gray
from skimage.filters import threshold_sauvola

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "layout_segmenter.onnx")
RESIZE_TO = (1344, 2016)  # (alto, ancho) -- igual que el notebook de entrenamiento
PATCH_SIZE = 672
CLASS_NAMES = {1: "Texto principal", 2: "Nota al margen"}
SAUVOLA_WINDOW = 31
SAUVOLA_K = 0.2
MIN_REGION_AREA = 2000  # descarta manchas ruidosas post-refinamiento
REGION_MERGE_KERNEL = (20, 25)  # (ancho, alto) en px sobre el resize 1344x2016 --
# punto de partida, falta calibrar contra el hueco real entre regiones vecinas en
# la GT de las 7 páginas marcadas a mano (ver nota al final).

_session = None


def _get_session() -> ort.InferenceSession:
    global _session
    if _session is None:
        _session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return _session


def _predict_grid(session: ort.InferenceSession, img_resized: np.ndarray) -> np.ndarray:
    """Corre el modelo sobre el grid de parches base (sin solape), igual que en entrenamiento."""
    h, w = img_resized.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    input_name = session.get_inputs()[0].name

    for y in range(0, h - PATCH_SIZE + 1, PATCH_SIZE):
        for x in range(0, w - PATCH_SIZE + 1, PATCH_SIZE):
            patch = img_resized[y:y + PATCH_SIZE, x:x + PATCH_SIZE]
            input_tensor = patch.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
            logits = session.run(None, {input_name: input_tensor})[0]
            mask[y:y + PATCH_SIZE, x:x + PATCH_SIZE] = logits[0].argmax(axis=0).astype(np.uint8)

    return mask


def _refine_with_sauvola(img_resized: np.ndarray, coarse_mask: np.ndarray) -> np.ndarray:
    gray = rgb2gray(img_resized)
    thresh = threshold_sauvola(gray, window_size=SAUVOLA_WINDOW, k=SAUVOLA_K)
    ink = gray < thresh
    refined = coarse_mask.copy()
    refined[(coarse_mask > 0) & ~ink] = 0
    return refined

def _group_ink_to_instances(class_mask: np.ndarray, kernel_size: Tuple[int, int]) -> np.ndarray:
    """
    Agrupa tinta dispersa (letras/líneas sueltas) en instancias de región completas:
    cierra huecos con un kernel grande para conectar componentes, etiqueta cada
    blob conectado, y devuelve un mapa de labels (0 = fondo).
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    closed = cv2.morphologyEx(class_mask, cv2.MORPH_CLOSE, kernel)
    _, labels = cv2.connectedComponents(closed)
    return labels

def segment_by_ml(image_path: str) -> List[dict]:
    """
    Args:
        image_path: ruta absoluta a la imagen del documento

    Returns:
        Lista de dicts con: x, y, width, height, region_type, confidence, order_index
    """
    session = _get_session()

    original = cv2.imread(image_path)
    original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    orig_h, orig_w = original.shape[:2]

    resized = cv2.resize(original, (RESIZE_TO[1], RESIZE_TO[0]))
    coarse = _predict_grid(session, resized)
    refined = _refine_with_sauvola(resized, coarse)

    scale_x = orig_w / RESIZE_TO[1]
    scale_y = orig_h / RESIZE_TO[0]

    results = []
    order_index = 0
    for class_id, type_name in CLASS_NAMES.items():
        class_mask = (refined == class_id).astype(np.uint8) * 255
        labels = _group_ink_to_instances(class_mask, REGION_MERGE_KERNEL)

        for label in range(1, labels.max() + 1):
            instance_ink = np.where(labels == label, class_mask, 0).astype(np.uint8)
            points = cv2.findNonZero(instance_ink)
            if points is None:
                continue
            x, y, w, h = cv2.boundingRect(points)
            if w * h < MIN_REGION_AREA:
                continue
            results.append({
                "x": int(x * scale_x),
                "y": int(y * scale_y),
                "width": int(w * scale_x),
                "height": int(h * scale_y),
                "region_type": type_name,
                "confidence": 0.8,
                "order_index": order_index,
            })
            order_index += 1

    return results