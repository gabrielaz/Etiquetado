"""Extraccion de parches: grilla no solapada + crops aleatorios.

La grilla es determinista y cubre la pagina exacta. Los crops aleatorios se
regeneran en cada epoca (Dynamic Instance Generation del paper).
"""

import numpy as np


def parches_grilla(arr: np.ndarray, patch_size: int) -> np.ndarray:
    alto, ancho = arr.shape[:2]
    if alto % patch_size or ancho % patch_size:
        raise ValueError(
            f"la pagina {alto}x{ancho} no es divisible por el parche {patch_size}"
        )

    filas, cols = alto // patch_size, ancho // patch_size
    salida = [
        arr[
            f * patch_size : (f + 1) * patch_size,
            c * patch_size : (c + 1) * patch_size,
        ]
        for f in range(filas)
        for c in range(cols)
    ]
    return np.stack(salida)


def crops_aleatorios(
    img: np.ndarray,
    mask: np.ndarray,
    patch_size: int,
    n: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    alto, ancho = img.shape[:2]
    ys = rng.integers(0, alto - patch_size + 1, size=n)
    xs = rng.integers(0, ancho - patch_size + 1, size=n)

    crops_img = np.stack(
        [img[y : y + patch_size, x : x + patch_size] for y, x in zip(ys, xs)]
    )
    crops_msk = np.stack(
        [mask[y : y + patch_size, x : x + patch_size] for y, x in zip(ys, xs)]
    )
    return crops_img, crops_msk
