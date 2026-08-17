"""Loss de la fase 1: CrossEntropy ponderada por frecuencia inversa de clase.

Los pesos vienen de train.py del repo oficial. Los denominadores son valores
aproximados de la frecuencia porcentual de cada clase; no coinciden exacto con
la distribucion medida sobre las 2 imagenes de training (ver test_gt.py), asi
que se toman como lo que son -- pesos de la loss, no una medicion.

Orden de clases: [fondo, comment, decoration, text].
"""

import numpy as np
import torch
import torch.nn as nn

PESOS_CE: dict[str, np.ndarray] = {
    "CB55": np.sqrt([1.0 / 82, 1.0 / 8.36, 1.0 / 0.55, 1.0 / 8.68]),
    "CS18": np.sqrt([1.0 / 85, 1.0 / 6.78, 1.0 / 1.47, 1.0 / 6.59]),
    "CS863": np.sqrt([1.0 / 78, 1.0 / 6.35, 1.0 / 1.83, 1.0 / 14]),
}


def crear_ce_ponderada(manuscrito: str, device: str = "cpu") -> nn.CrossEntropyLoss:
    """CrossEntropy ponderada. Espera LOGITS crudos, no probabilidades:
    nn.CrossEntropyLoss ya aplica log-softmax internamente.

    El repo oficial aplica torch.softmax antes de llamarla, lo que es un bug
    (aplasta los gradientes). Aca se pasa el tensor de logits sin transformar.
    """
    pesos = torch.tensor(PESOS_CE[manuscrito], dtype=torch.float32, device=device)
    return nn.CrossEntropyLoss(weight=pesos)
