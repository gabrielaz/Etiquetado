"""Dataset de DIVA-HisDB: una pagina -> 34 parches (24 de grilla + 10 crops).

El GT se decodifica ANTES del resize y se reescala con vecino mas cercano,
para no inventar etiquetas intermedias por interpolacion.

Imagen y GT se emparejan por NOMBRE de archivo, no por posicion: la carpeta
CS18/pixel-level-gt-CS18/training del repo oficial trae 20 GT para solo 2
imagenes, y los huerfanos quedan intercalados alfabeticamente entre los
correctos. Emparejar por indice asignaria GT equivocado sin avisar.
"""

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from paper_replica.config import DIVA_ROOT, SEED, Config
from paper_replica.data.gt import decodificar_gt_diva
from paper_replica.data.patches import crops_aleatorios, parches_grilla


def cargar_pagina(
    img_path: Path, gt_path: Path, cfg: Config
) -> tuple[np.ndarray, np.ndarray]:
    img = Image.open(img_path).convert("RGB").resize(
        (cfg.img_w, cfg.img_h), Image.BILINEAR
    )

    gt_rgb = np.array(Image.open(gt_path).convert("RGB"))
    mask = decodificar_gt_diva(gt_rgb)
    mask = np.array(
        Image.fromarray(mask.astype(np.uint8)).resize(
            (cfg.img_w, cfg.img_h), Image.NEAREST
        )
    ).astype(np.int64)

    return np.array(img), mask


class DivaDataset(Dataset):
    def __init__(
        self,
        manuscrito: str,
        split: str,
        cfg: Config,
        con_crops: bool,
        root: Path | None = None,
    ):
        self.cfg = cfg
        self.con_crops = con_crops
        self.manuscrito = manuscrito
        self.epoch = 0

        base = (root or DIVA_ROOT) / manuscrito
        dir_img = base / f"img-{manuscrito}" / split
        dir_gt = base / f"pixel-level-gt-{manuscrito}" / split

        self.img_paths = sorted(dir_img.glob("*"))
        gt_por_stem = {p.stem: p for p in dir_gt.glob("*")}

        faltantes = [p.stem for p in self.img_paths if p.stem not in gt_por_stem]
        if faltantes:
            raise FileNotFoundError(
                f"{manuscrito}/{split}: sin GT para {', '.join(faltantes)}"
            )

        self.gt_paths = [gt_por_stem[p.stem] for p in self.img_paths]

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __len__(self) -> int:
        return len(self.img_paths)

    def __getitem__(self, idx: int):
        img, mask = cargar_pagina(self.img_paths[idx], self.gt_paths[idx], self.cfg)

        p_img = parches_grilla(img, self.cfg.patch_size)
        p_msk = parches_grilla(mask, self.cfg.patch_size)

        if self.con_crops:
            rng = np.random.default_rng(SEED + self.epoch * 1000 + idx)
            c_img, c_msk = crops_aleatorios(
                img, mask, self.cfg.patch_size, self.cfg.n_crops, rng
            )
            p_img = np.concatenate([p_img, c_img])
            p_msk = np.concatenate([p_msk, c_msk])

        # (N, H, W, C) -> (N, C, H, W), escalado a [0,1] como el ToTensor oficial
        patches = torch.from_numpy(p_img).permute(0, 3, 1, 2).float() / 255.0
        masks = torch.from_numpy(p_msk).long()
        return patches, masks
