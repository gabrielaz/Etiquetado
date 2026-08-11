import numpy as np
import pytest

from paper_replica.data.patches import parches_grilla
from paper_replica.evaluate import (
    f1_binario_macro,
    f1_clase,
    mascara_tinta,
    matriz_confusion,
    reensamblar,
    refinar,
)


def test_f1_de_gt_contra_si_mismo_es_exactamente_1(mascara_sintetica):
    """Sanity check numero uno: valida el evaluador antes de juzgar al modelo."""
    for clase in (1, 2, 3):
        assert f1_clase(mascara_sintetica, mascara_sintetica, clase) == 1.0
        assert f1_binario_macro(mascara_sintetica, mascara_sintetica, clase) == 1.0


def test_f1_de_prediccion_vacia_es_cero(mascara_sintetica):
    vacia = np.zeros_like(mascara_sintetica)
    assert f1_clase(vacia, mascara_sintetica, 3) == 0.0


def test_f1_conocido_a_mano():
    # 4 pixeles de clase 1 en el GT, el modelo acierta 2 y agrega 1 falso
    gt = np.array([[1, 1, 1, 1, 0, 0]])
    pred = np.array([[1, 1, 0, 0, 1, 0]])
    # TP=2, FP=1, FN=2 -> P=2/3, R=1/2, F1=2*(2/3*1/2)/(2/3+1/2)=0.5714...
    assert f1_clase(pred, gt, 1) == pytest.approx(0.5714285, abs=1e-6)


def test_las_dos_variantes_difieren_cuando_el_fondo_domina():
    """La variante B promedia con el F1 del fondo, que es facil de acertar,
    asi que sube el numero. Es la ambiguedad del paper (ver diseno seccion 8)."""
    gt = np.zeros((100, 100), dtype=np.int64)
    gt[:5, :5] = 3
    pred = np.zeros((100, 100), dtype=np.int64)
    pred[:4, :5] = 3
    a = f1_clase(pred, gt, 3)
    b = f1_binario_macro(pred, gt, 3)
    assert b > a


def test_otra_clase_cuenta_como_fondo():
    """El paper mapea la otra clase a fondo en pred y gt a la vez."""
    gt = np.array([[3, 3, 1, 1]])
    pred = np.array([[3, 3, 1, 1]])
    assert f1_clase(pred, gt, 3) == 1.0


def test_reensamblar_es_la_inversa_de_la_grilla(cfg):
    original = np.arange(cfg.img_h * cfg.img_w).reshape(cfg.img_h, cfg.img_w)
    p = parches_grilla(original, cfg.patch_size)
    assert np.array_equal(reensamblar(p, cfg), original)


def test_reensamblar_conserva_los_canales(pagina_sintetica, cfg):
    """La cadena de refinamiento necesita la pagina RGB completa, no solo
    la mascara de etiquetas."""
    p = parches_grilla(pagina_sintetica, cfg.patch_size)
    out = reensamblar(p, cfg)
    assert out.shape == (cfg.img_h, cfg.img_w, 3)
    assert np.array_equal(out, pagina_sintetica)


def test_matriz_confusion_diagonal_para_prediccion_perfecta(mascara_sintetica):
    m = matriz_confusion(mascara_sintetica, mascara_sintetica, 4)
    assert np.array_equal(m, np.diag(np.diag(m)))
    assert m.sum() == mascara_sintetica.size


def test_mascara_tinta_detecta_lo_oscuro(cfg):
    img = np.full((100, 100, 3), 240, dtype=np.uint8)
    img[40:60, 40:60] = 20
    tinta = mascara_tinta(img, cfg.sauvola_window, cfg.sauvola_k)
    assert tinta[50, 50]
    assert not tinta[5, 5]


def test_refinar_borra_prediccion_donde_no_hay_tinta(cfg):
    img = np.full((100, 100, 3), 240, dtype=np.uint8)
    img[40:60, 40:60] = 20
    pred = np.full((100, 100), 3, dtype=np.int64)
    out = refinar(pred, img, cfg, min_size=0)
    assert out[50, 50] == 3
    assert out[5, 5] == 0


def test_sauvola_no_marca_tinta_en_una_imagen_uniforme(cfg):
    """Sin variacion local, el umbral de Sauvola queda por debajo del propio
    gris y no detecta nada. Vale la pena fijarlo: una pagina sin contraste
    hace que el refinamiento borre toda la prediccion."""
    plana = np.full((100, 100, 3), 20, dtype=np.uint8)
    assert not mascara_tinta(plana, cfg.sauvola_window, cfg.sauvola_k).any()


def test_sauvola_solo_marca_el_borde_de_bloques_mas_grandes_que_la_ventana(cfg):
    """En el interior de una mancha mas ancha que la ventana (31 px) tampoco
    hay variacion local, asi que Sauvola marca el contorno y no el relleno.
    No afecta a manuscritos reales, donde la tinta son trazos finos."""
    img = np.full((200, 200, 3), 240, dtype=np.uint8)
    img[50:150, 50:150] = 20  # bloque de 100x100, muy mayor que la ventana
    tinta = mascara_tinta(img, cfg.sauvola_window, cfg.sauvola_k)
    assert tinta[52, 52]        # borde: si
    assert not tinta[100, 100]  # centro: no


def test_refinar_elimina_componentes_chicos(cfg):
    # tinta oscura sobre fondo claro, en bloques menores que la ventana de
    # Sauvola para que quede detectada por completo
    img = np.full((200, 200, 3), 240, dtype=np.uint8)
    img[20:40, 20:40] = 20      # 400 px
    img[100:102, 100:102] = 20  # 4 px

    pred = np.zeros((200, 200), dtype=np.int64)
    pred[20:40, 20:40] = 3
    pred[100:102, 100:102] = 3

    sin_limpiar = refinar(pred, img, cfg, min_size=0)
    assert sin_limpiar[30, 30] == 3 and sin_limpiar[100, 100] == 3

    out = refinar(pred, img, cfg, min_size=100)
    assert out[30, 30] == 3
    assert out[100, 100] == 0


def test_evaluar_gt_contra_gt_da_1(diva_disponible, cfg):
    """Ultima verificacion del evaluador con datos reales, sin modelo."""
    from paper_replica.data.dataset import DivaDataset

    ds = DivaDataset("CB55", "validation", cfg, con_crops=False)
    _, masks = ds[0]
    gt = reensamblar(masks.numpy(), cfg)
    for clase in (1, 2, 3):
        if (gt == clase).any():
            assert f1_clase(gt, gt, clase) == 1.0
