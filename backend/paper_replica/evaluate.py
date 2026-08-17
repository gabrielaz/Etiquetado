"""Metricas y refinamiento de predicciones.

Sobre la pagina completa reensamblada, nunca sobre parches sueltos.

El paper 2024 define el F1 por clase "conservando unicamente los pixeles de la
clase de interes y estableciendo todos los pixeles de la otra clase como
fondo". Eso deja ambiguo que se hace con el fondo, asi que se implementan las
dos lecturas y se reporta cual reproduce los numeros publicados:
  - f1_clase: F1 solo de la clase de interes (equivale a one-vs-rest)
  - f1_binario_macro: media del F1 de la clase y del fondo
"""

import numpy as np
from skimage.color import rgb2gray
from skimage.filters import threshold_sauvola
from skimage.morphology import remove_small_objects

from paper_replica.config import Config


def reensamblar(parches: np.ndarray, cfg: Config) -> np.ndarray:
    """Inversa de parches_grilla. Acepta (N, ps, ps) y (N, ps, ps, C)."""
    cols = cfg.grid_cols
    ps = cfg.patch_size
    forma = (cfg.img_h, cfg.img_w) + parches.shape[3:]
    salida = np.zeros(forma, dtype=parches.dtype)
    for i, p in enumerate(parches):
        f, c = divmod(i, cols)
        salida[f * ps : (f + 1) * ps, c * ps : (c + 1) * ps] = p
    return salida


def _f1(pred_bin: np.ndarray, gt_bin: np.ndarray) -> float:
    tp = int(np.sum(pred_bin & gt_bin))
    fp = int(np.sum(pred_bin & ~gt_bin))
    fn = int(np.sum(~pred_bin & gt_bin))
    if tp == 0:
        return 0.0
    return 2 * tp / (2 * tp + fp + fn)


def f1_clase(pred: np.ndarray, gt: np.ndarray, clase: int) -> float:
    """Variante A: F1 de la clase de interes."""
    return _f1(pred == clase, gt == clase)


def f1_binario_macro(pred: np.ndarray, gt: np.ndarray, clase: int) -> float:
    """Variante B: media del F1 de la clase y del F1 del fondo."""
    pos = _f1(pred == clase, gt == clase)
    neg = _f1(pred != clase, gt != clase)
    return (pos + neg) / 2


def matriz_confusion(pred: np.ndarray, gt: np.ndarray, n_classes: int) -> np.ndarray:
    idx = gt.ravel() * n_classes + pred.ravel()
    return np.bincount(idx, minlength=n_classes**2).reshape(n_classes, n_classes)


def metricas_desde_confusion(cm: np.ndarray) -> dict:
    """Metricas del repo oficial, derivadas de la matriz de confusion.

    `cm[i, j]` = pixeles con gt==i y pred==j.

    test.py de axelden/Few-shot-DIA-WACV2023 llama a `get_scores(average=...)`,
    que son las funciones de sklearn sobre la concatenacion plana de todos los
    pixeles del split, con las 4 clases y el fondo incluido. Los numeros del
    README son la variante `weighted`; `macro` se imprime debajo.

    Se calcula en forma cerrada desde la matriz en vez de guardar los arrays de
    pixeles: la matriz es estadistico suficiente para cualquier agregacion, pesa
    unos pocos bytes y permite recalcular sin el modelo ni la GPU. Los tests
    verifican paridad exacta con sklearn.
    """
    cm = np.asarray(cm, dtype=np.float64)
    tp = np.diag(cm)
    soporte = cm.sum(axis=1)  # pixeles reales de cada clase (gt)
    predichos = cm.sum(axis=0)
    fp = predichos - tp
    fn = soporte - tp

    def _div(num, den):
        return np.divide(num, den, out=np.zeros_like(num), where=den > 0)

    por_clase = {
        "precision": _div(tp, tp + fp),
        "recall": _div(tp, tp + fn),
        "f1": _div(2 * tp, 2 * tp + fp + fn),
        "iou": _div(tp, tp + fp + fn),
    }

    # sklearn promedia sobre las etiquetas presentes en y_true o en y_pred; una
    # clase ausente de ambos no debe arrastrar el macro hacia cero
    presentes = (soporte > 0) | (predichos > 0)
    total = cm.sum()

    resultado = {
        "accuracy": float(tp.sum() / total) if total > 0 else 0.0,
        "soporte": soporte.astype(np.int64).tolist(),
        "por_clase": {k: v.tolist() for k, v in por_clase.items()},
    }
    for nombre, pesos in (("macro", presentes.astype(np.float64)), ("weighted", soporte)):
        suma = pesos.sum()
        resultado[nombre] = {
            k: float(np.dot(v, pesos) / suma) if suma > 0 else 0.0
            for k, v in por_clase.items()
        }
    return resultado


def mascara_tinta(img_rgb: np.ndarray, window_size: int, k: float) -> np.ndarray:
    gris = rgb2gray(img_rgb)
    return gris < threshold_sauvola(gris, window_size=window_size, k=k)


def refinar(
    pred: np.ndarray, img_rgb: np.ndarray, cfg: Config, min_size: int = 64
) -> np.ndarray:
    """Cadena de refinamiento del repo oficial: multiplicar por la mascara de
    tinta y despues eliminar componentes conexos chicos, clase por clase."""
    tinta = mascara_tinta(img_rgb, cfg.sauvola_window, cfg.sauvola_k)
    out = pred * tinta

    if min_size > 0:
        for clase in range(1, cfg.n_classes):
            binaria = out == clase
            limpia = remove_small_objects(binaria, min_size=min_size)
            out[binaria & ~limpia] = 0

    return out.astype(np.int64)
