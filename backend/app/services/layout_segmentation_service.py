
"""
Servicio heuristico de segmentacion de layout: agrupa las cajas de palabras ya
detectadas en un documento en bloques ("regiones") y clasifica cada uno como
"Texto principal" o "Nota al margen".

Version 2: agrupa por proximidad 2D (no solo por columnas en X). La primera
version agrupaba solo proyectando en el eje X, pero al probarla contra la GT
real (test_layout_segmentation.py) colapsaba la pagina entera en una sola
region: palabras de bloques distintos pero a distinta altura (ej. un
encabezado que cruza casi toda la pagina) igual puenteaban el hueco en X y
fusionaban columnas que en realidad estaban separadas verticalmente. Agrupar
tambien por Y evita ese puente falso.

Calibrado contra GT real (ver backend/scripts/analyze_layout_gt.py, proyecto 1):
    Texto principal ocupa 33%-42% del ancho de la pagina.
    Nota al margen ocupa 9%-17% del ancho de la pagina.
"""

from typing import List

WIDTH_RATIO_THRESHOLD = 0.25  # punto medio del hueco 0.17-0.33 hallado en la calibracion
GAP_RATIO = 0.015             # separacion minima (relativa al ancho de pagina) para NO fusionar dos palabras en el mismo bloque


def _expand(word: dict, gap: float) -> tuple:
    return (
        word["x"] - gap,
        word["y"] - gap,
        word["x"] + word["width"] + gap,
        word["y"] + word["height"] + gap,
    )


def _overlaps(a: tuple, b: tuple) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _cluster_words(words: List[dict], gap: float) -> List[List[dict]]:
    """
    Agrupa palabras en bloques por adyacencia 2D: dos palabras quedan en el
    mismo bloque si, al expandir sus bboxes por gap en las 4 direcciones, se
    tocan o se superponen. Usa union-find sobre todos los pares.
    """
    n = len(words)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    expanded = [_expand(w, gap) for w in words]
    for i in range(n):
        for j in range(i + 1, n):
            if _overlaps(expanded[i], expanded[j]):
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(words[i])
    return list(groups.values())


def segment_layout_regions(words: List[dict], page_width: float) -> List[dict]:
    """
    Args:
        words: lista de dicts con x, y, width, height (bboxes de Word ya existentes)
        page_width: ancho de la pagina en pixeles (Document.image_width)

    Returns:
        Lista de dicts con: x, y, width, height, region_type, n_words,
        confidence, order_index
    """
    if not words:
        return []

    gap = page_width * GAP_RATIO
    clusters = _cluster_words(words, gap)

    results = []
    for idx, cluster in enumerate(clusters):
        x0 = min(w["x"] for w in cluster)
        y0 = min(w["y"] for w in cluster)
        x1 = max(w["x"] + w["width"] for w in cluster)
        y1 = max(w["y"] + w["height"] for w in cluster)
        width = x1 - x0

        width_ratio = width / page_width
        region_type = "Texto principal" if width_ratio >= WIDTH_RATIO_THRESHOLD else "Nota al margen"

        results.append({
            "x": int(x0),
            "y": int(y0),
            "width": int(width),
            "height": int(y1 - y0),
            "region_type": region_type,
            "n_words": len(cluster),
            "confidence": 0.7,
            "order_index": idx,
        })

    return results