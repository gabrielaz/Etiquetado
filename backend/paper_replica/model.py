"""DeepLabv3+ configurable.

Fase 1 replica el repo oficial: resnet50 sin preentrenar, 4 clases.
La fase 2 cambiara el backbone a Xception con pesos ImageNet.
"""

import segmentation_models_pytorch as smp
import torch

from paper_replica.config import Config


def crear_modelo(cfg: Config) -> smp.DeepLabV3Plus:
    return smp.DeepLabV3Plus(
        encoder_name=cfg.backbone,
        encoder_weights=cfg.encoder_weights,
        in_channels=3,
        classes=cfg.n_classes,
    )


def rango_logits(model: torch.nn.Module, entrada: torch.Tensor) -> float:
    """Magnitud maxima de los logits. Guardia contra la degeneracion de
    BatchNorm que en el intento anterior producia valores de ~1e20."""
    model.eval()
    with torch.no_grad():
        salida = model(entrada)
    return float(salida.abs().max())
