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
    reensamblar,
    refinar,
)
from paper_replica.model import crear_modelo

NOMBRES_CLASE = {1: "comment", 2: "decoration", 3: "text"}

# README del repo oficial axelden/Few-shot-DIA-WACV2023
F1_OFICIAL = {"CB55": 0.991, "CS18": 0.984, "CS863": 0.975}
TOLERANCIA = 0.02


def evaluar_manuscrito(
    manuscrito: str,
    state_dict: dict,
    cfg: Config,
    device: str = "cuda",
    split: str = "public-test",
    refinamiento: bool = True,
) -> dict:
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
            pred = refinar(pred, reensamblar(img_patches, cfg), cfg)

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
        "f1_variante_a": {NOMBRES_CLASE[c]: float(np.mean(v)) for c, v in f1_a.items()},
        "f1_variante_b": {NOMBRES_CLASE[c]: float(np.mean(v)) for c, v in f1_b.items()},
        "media_a": float(np.mean([np.mean(v) for v in f1_a.values()])),
        "media_b": float(np.mean([np.mean(v) for v in f1_b.values()])),
        "confusion": confusion.tolist(),
        "max_logit": max_logit,
    }


def imprimir_veredicto(resultados: list[dict]) -> bool:
    """Contrasta contra el criterio de aceptacion de la fase 1. Devuelve True
    si los tres manuscritos entran en la tolerancia con alguna variante."""
    print(f"{'manuscrito':<10} {'variante':<10} {'obtenido':>9} "
          f"{'oficial':>8} {'delta':>8}  estado")
    print("-" * 58)

    pasa_todo = True
    for r in resultados:
        oficial = F1_OFICIAL[r["manuscrito"]]
        ok_alguna = False
        for variante, clave in (("A", "media_a"), ("B", "media_b")):
            delta = r[clave] - oficial
            # redondeo para que el borde exacto de la tolerancia entre: la
            # resta en punto flotante deja residuos de ~1e-17
            ok = round(abs(delta), 6) <= TOLERANCIA
            ok_alguna = ok_alguna or ok
            print(
                f"{r['manuscrito']:<10} {variante:<10} {r[clave]:>9.4f} "
                f"{oficial:>8.3f} {delta:>+8.4f}  {'OK' if ok else 'FUERA'}"
            )
        pasa_todo = pasa_todo and ok_alguna

    print()
    print("FASE 1 SUPERADA" if pasa_todo else "FASE 1 NO SUPERADA -- no avanzar")
    return pasa_todo
