import numpy as np
import pytest
import torch

from paper_replica.data.dataset import DivaDataset, cargar_pagina


def test_item_devuelve_34_parches_con_crops(diva_disponible, cfg):
    ds = DivaDataset("CB55", "training", cfg, con_crops=True)
    patches, masks = ds[0]
    assert patches.shape == (34, 3, 336, 336)
    assert masks.shape == (34, 336, 336)


def test_item_devuelve_24_parches_sin_crops(diva_disponible, cfg):
    ds = DivaDataset("CB55", "validation", cfg, con_crops=False)
    patches, masks = ds[0]
    assert patches.shape == (24, 3, 336, 336)
    assert masks.shape == (24, 336, 336)


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_split_training_tiene_2_paginas(diva_disponible, cfg, manuscrito):
    """El escenario few-shot del paper: 2 imagenes de entrenamiento.

    CS18 trae 20 GT para 2 imagenes en su carpeta de training; el dataset debe
    quedarse con los 2 que corresponden, no con los 20.
    """
    ds = DivaDataset(manuscrito, "training", cfg, con_crops=True)
    assert len(ds) == 2


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_imagen_y_gt_se_emparejan_por_nombre(diva_disponible, cfg, manuscrito):
    """Emparejar por posicion daria GT equivocado en CS18, que tiene GT
    huerfanos intercalados alfabeticamente entre los correctos."""
    ds = DivaDataset(manuscrito, "training", cfg, con_crops=False)
    for img_p, gt_p in zip(ds.img_paths, ds.gt_paths):
        assert img_p.stem == gt_p.stem


def test_cs18_elige_las_paginas_correctas(diva_disponible, cfg):
    ds = DivaDataset("CS18", "training", cfg, con_crops=False)
    assert {p.stem for p in ds.img_paths} == {
        "e-codices_csg-0018_099_max",
        "e-codices_csg-0018_105_max",
    }


def test_error_si_falta_el_gt_de_una_imagen(diva_disponible, cfg, tmp_path):
    """Una imagen sin GT debe fallar ruidosamente, no saltearse en silencio."""
    base = tmp_path / "XX"
    (base / "img-XX" / "training").mkdir(parents=True)
    (base / "pixel-level-gt-XX" / "training").mkdir(parents=True)
    (base / "img-XX" / "training" / "pagina_a.jpg").touch()

    with pytest.raises(FileNotFoundError, match="pagina_a"):
        DivaDataset("XX", "training", cfg, con_crops=False, root=tmp_path)


def test_tipos_y_rango_de_valores(diva_disponible, cfg):
    ds = DivaDataset("CB55", "training", cfg, con_crops=False)
    patches, masks = ds[0]
    assert patches.dtype == torch.float32
    assert masks.dtype == torch.int64
    # ToTensor escala a [0,1]; NO hay normalizacion ImageNet en fase 1
    assert 0.0 <= patches.min() and patches.max() <= 1.0
    assert 0 <= masks.min() and masks.max() <= 3


def test_set_epoch_regenera_los_crops(diva_disponible, cfg):
    """Dynamic Instance Generation: los crops cambian en cada epoca."""
    ds = DivaDataset("CB55", "training", cfg, con_crops=True)
    ds.set_epoch(0)
    a, _ = ds[0]
    ds.set_epoch(1)
    b, _ = ds[0]
    # los primeros 24 son la grilla fija: identicos
    assert torch.equal(a[:24], b[:24])
    # los ultimos 10 son crops: distintos
    assert not torch.equal(a[24:], b[24:])


def test_misma_epoca_da_los_mismos_crops(diva_disponible, cfg):
    ds = DivaDataset("CB55", "training", cfg, con_crops=True)
    ds.set_epoch(3)
    a, _ = ds[0]
    ds.set_epoch(3)
    b, _ = ds[0]
    assert torch.equal(a, b)


def test_imagen_y_mascara_tienen_el_mismo_tamano_tras_resize(diva_disponible, cfg):
    ds = DivaDataset("CB55", "training", cfg, con_crops=False)
    img, msk = cargar_pagina(ds.img_paths[0], ds.gt_paths[0], cfg)
    assert img.shape == (cfg.img_h, cfg.img_w, 3)
    assert msk.shape == (cfg.img_h, cfg.img_w)
    assert set(np.unique(msk)) <= {0, 1, 2, 3}
