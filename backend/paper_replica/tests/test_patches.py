import numpy as np
import pytest

from paper_replica.data.patches import crops_aleatorios, parches_grilla


def test_grilla_cubre_la_pagina_exacta(pagina_sintetica, cfg):
    p = parches_grilla(pagina_sintetica, cfg.patch_size)
    assert p.shape == (24, 336, 336, 3)


def test_grilla_sobre_mascara_2d(mascara_sintetica, cfg):
    p = parches_grilla(mascara_sintetica, cfg.patch_size)
    assert p.shape == (24, 336, 336)
    assert p.dtype == mascara_sintetica.dtype


def test_grilla_no_pierde_ni_duplica_pixeles(cfg):
    """Cada pixel de la pagina aparece exactamente una vez en la grilla."""
    total = cfg.img_h * cfg.img_w
    unicos = np.arange(total).reshape(cfg.img_h, cfg.img_w)
    p = parches_grilla(unicos, cfg.patch_size)
    assert np.array_equal(np.sort(p.ravel()), np.arange(total))


def test_grilla_rechaza_tamano_no_divisible(cfg):
    arr = np.zeros((100, 100), dtype=np.int64)
    with pytest.raises(ValueError, match="divisible"):
        parches_grilla(arr, cfg.patch_size)


def test_crops_devuelven_la_cantidad_pedida(pagina_sintetica, mascara_sintetica, cfg):
    rng = np.random.default_rng(42)
    img, msk = crops_aleatorios(
        pagina_sintetica, mascara_sintetica, cfg.patch_size, cfg.n_crops, rng
    )
    assert img.shape == (10, 336, 336, 3)
    assert msk.shape == (10, 336, 336)


def test_crops_son_deterministas_con_la_misma_semilla(
    pagina_sintetica, mascara_sintetica, cfg
):
    a, _ = crops_aleatorios(
        pagina_sintetica, mascara_sintetica, cfg.patch_size, 5, np.random.default_rng(1)
    )
    b, _ = crops_aleatorios(
        pagina_sintetica, mascara_sintetica, cfg.patch_size, 5, np.random.default_rng(1)
    )
    assert np.array_equal(a, b)


def test_crops_cambian_entre_semillas(pagina_sintetica, mascara_sintetica, cfg):
    """La generacion dinamica de instancias exige parches distintos por epoca."""
    a, _ = crops_aleatorios(
        pagina_sintetica, mascara_sintetica, cfg.patch_size, 5, np.random.default_rng(1)
    )
    b, _ = crops_aleatorios(
        pagina_sintetica, mascara_sintetica, cfg.patch_size, 5, np.random.default_rng(2)
    )
    assert not np.array_equal(a, b)


def test_crop_e_imagen_quedan_alineados(cfg):
    """El crop de la imagen y el de la mascara deben salir de la misma posicion."""
    img = np.arange(cfg.img_h * cfg.img_w, dtype=np.int64).reshape(cfg.img_h, cfg.img_w)
    img3 = np.stack([img, img, img], axis=-1)
    ci, cm = crops_aleatorios(img3, img, cfg.patch_size, 4, np.random.default_rng(7))
    assert np.array_equal(ci[:, :, :, 0], cm)
