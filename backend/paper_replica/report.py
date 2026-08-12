"""Evaluacion de un manuscrito entero sobre el split de test.

Devuelve las dos variantes de F1 (ver evaluate.py) para poder decidir cual de
las dos lecturas del paper reproduce los numeros publicados.
"""

import numpy as np
import torch

from paper_replica.config import Config
from paper_replica.data.dataset import DivaDataset
from paper_replica.evaluate import (
    f1_binario_macro,
    f1_clase,
    matriz_confusion,
    metricas_desde_confusion,
    reensamblar,
    refinar,
)
from paper_replica.model import crear_modelo

NOMBRES_CLASE = {1: "comment", 2: "decoration", 3: "text"}

# Tabla del README del repo oficial axelden/Few-shot-DIA-WACV2023.
# Son la salida de get_scores(average="weighted"): sklearn sobre todos los
# pixeles del split juntos, las 4 clases, fondo incluido.
METRICAS_OFICIALES = {
    "CB55": {"precision": 0.991, "recall": 0.991, "iou": 0.982, "f1": 0.991},
    "CS18": {"precision": 0.984, "recall": 0.984, "iou": 0.970, "f1": 0.984},
    "CS863": {"precision": 0.977, "recall": 0.974, "iou": 0.956, "f1": 0.975},
}
F1_OFICIAL = {m: v["f1"] for m, v in METRICAS_OFICIALES.items()}
TOLERANCIA = 0.02


def evaluar_manuscrito(
    manuscrito: str,
    state_dict: dict,
    cfg: Config,
    device: str = "cuda",
    split: str = "public-test",
    refinamiento: bool = True,
    min_size: int = 0,
) -> dict:
    """min_size=0 por defecto: test.py del repo oficial importa removeSmallCC
    pero nunca lo llama. Su refinamiento es solo la multiplicacion por la
    mascara de tinta de Sauvola."""
    ds = DivaDataset(manuscrito, split, cfg, con_crops=False)

    model = crear_modelo(cfg).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    f1_a = {c: [] for c in NOMBRES_CLASE}
    f1_b = {c: [] for c in NOMBRES_CLASE}
    confusion = np.zeros((cfg.n_classes, cfg.n_classes), dtype=np.int64)
    max_logit = 0.0

    for idx in range(len(ds)):
        patches, masks = ds[idx]

        preds = []
        with torch.no_grad():
            for i in range(0, len(patches), cfg.micro_batch):
                out = model(patches[i : i + cfg.micro_batch].to(device))
                max_logit = max(max_logit, float(out.abs().max()))
                preds.append(out.argmax(1).cpu())

        pred = reensamblar(torch.cat(preds).numpy(), cfg)
        gt = reensamblar(masks.numpy(), cfg)

        if refinamiento:
            img_patches = (patches.permute(0, 2, 3, 1).numpy() * 255).astype(np.uint8)
            pred = refinar(pred, reensamblar(img_patches, cfg), cfg, min_size=min_size)

        for c in NOMBRES_CLASE:
            f1_a[c].append(f1_clase(pred, gt, c))
            f1_b[c].append(f1_binario_macro(pred, gt, c))
        confusion += matriz_confusion(pred, gt, cfg.n_classes)

    if max_logit >= 1e3:
        raise RuntimeError(f"logits explotaron en evaluacion: {max_logit:.2e}")

    return {
        "manuscrito": manuscrito,
        "split": split,
        "refinamiento": refinamiento,
        "min_size": min_size,
        # la metrica que decide el veredicto: la del repo oficial
        "oficial": metricas_desde_confusion(confusion),
        # las dos lecturas del F1 del paper quedan como diagnostico: son macro
        # sobre las 3 clases de primer plano, no comparables con el README
        "f1_variante_a": {NOMBRES_CLASE[c]: float(np.mean(v)) for c, v in f1_a.items()},
        "f1_variante_b": {NOMBRES_CLASE[c]: float(np.mean(v)) for c, v in f1_b.items()},
        "media_a": float(np.mean([np.mean(v) for v in f1_a.values()])),
        "media_b": float(np.mean([np.mean(v) for v in f1_b.values()])),
        "confusion": confusion.tolist(),
        "max_logit": max_logit,
    }


def imprimir_veredicto(resultados: list[dict]) -> bool:
    """Contrasta contra el criterio de aceptacion de la fase 1.

    El veredicto se decide con la metrica del repo oficial (weighted sobre las
    4 clases, fondo incluido). Se imprimen las cuatro cifras publicadas, no solo
    el F1: reproducir el F1 y errarle al IoU significaria que la agregacion
    todavia no es la correcta.
    """
    print(f"{'manuscrito':<9} {'fuente':<9} {'prec':>8} {'rec':>8} "
          f"{'iou':>8} {'f1':>8}   estado")
    print("-" * 62)

    claves = ("precision", "recall", "iou", "f1")
    pasa_todo = True
    for r in resultados:
        pub = METRICAS_OFICIALES[r["manuscrito"]]
        obt = r["oficial"]["weighted"]
        # redondeo para que el borde exacto de la tolerancia entre: la resta en
        # punto flotante deja residuos de ~1e-17
        ok = round(abs(obt["f1"] - pub["f1"]), 6) <= TOLERANCIA
        pasa_todo = pasa_todo and ok

        print(f"{r['manuscrito']:<9} {'oficial':<9} "
              + " ".join(f"{pub[k]:>8.3f}" for k in claves))
        print(f"{'':9} {'nuestro':<9} "
              + " ".join(f"{obt[k]:>8.4f}" for k in claves)
              + f"   {'OK' if ok else 'FUERA'}")
        print(f"{'':9} {'delta':<9} "
              + " ".join(f"{obt[k] - pub[k]:>+8.4f}" for k in claves))
        print()

    print("FASE 1 SUPERADA" if pasa_todo else "FASE 1 NO SUPERADA -- no avanzar")
    return pasa_todo
