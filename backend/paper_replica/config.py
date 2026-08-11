"""Hiperparametros de la replica.

Los valores por defecto son los de la fase 1: replican train.py del repo
oficial axelden/Few-shot-DIA-WACV2023. La fase 2 los sobreescribira con los
del paper WACV 2024 (Xception, 672 px, Jaccard+Dice, 12 crops).

Ver docs/replica-denardin/2026-08-10-diseno.md
"""

from dataclasses import dataclass
from pathlib import Path

DIVA_ROOT = Path(__file__).resolve().parents[2] / "datos-diva" / "fewshot_data"

MANUSCRITOS = ("CB55", "CS18", "CS863")

SEED = 42


@dataclass(frozen=True)
class Config:
    img_w: int = 1344
    img_h: int = 2016
    patch_size: int = 336
    n_crops: int = 10

    backbone: str = "resnet50"
    encoder_weights: str | None = None
    n_classes: int = 4

    lr: float = 0.001
    weight_decay: float = 0.00001
    epochs: int = 200
    patience: int = 20
    min_epochs: int = 50

    micro_batch: int = 8
    use_amp: bool = False

    sauvola_window: int = 31
    sauvola_k: float = 0.01

    @property
    def grid_cols(self) -> int:
        return self.img_w // self.patch_size

    @property
    def grid_rows(self) -> int:
        return self.img_h // self.patch_size

    @property
    def patches_per_page(self) -> int:
        return self.grid_cols * self.grid_rows
