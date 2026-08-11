import numpy as np
import pytest

from paper_replica.data.gt import decodificar_gt_diva


def _rgb_con_azul(valores_azul):
    """Construye una imagen RGB donde el canal azul toma los valores dados."""
    arr = np.array(valores_azul, dtype=np.uint8).reshape(1, -1)
    rgb = np.zeros((*arr.shape, 3), dtype=np.uint8)
    rgb[:, :, 2] = arr
    return rgb


def test_mapea_cada_codigo_a_su_clase():
    # 8 y 10 -> text(3); 2 -> comment(1); 4, 6, 12 -> decoration(2)
    rgb = _rgb_con_azul([8, 10, 2, 4, 6, 12])
    out = decodificar_gt_diva(rgb, dilatar=False)
    assert out.tolist() == [[3, 3, 1, 2, 2, 2]]


def test_impares_son_fondo():
    # el bit menos significativo marca limite/ruido -> fondo
    rgb = _rgb_con_azul([9, 11, 3, 5])
    out = decodificar_gt_diva(rgb, dilatar=False)
    assert out.tolist() == [[0, 0, 0, 0]]


def test_rojo_128_gana_sobre_el_azul():
    # red_channel == 128 marca fondo aunque el azul diga otra cosa
    rgb = _rgb_con_azul([8, 8])
    rgb[0, 0, 0] = 128
    out = decodificar_gt_diva(rgb, dilatar=False)
    assert out.tolist() == [[0, 3]]


def test_dilatacion_expande_la_clase_de_indice_mayor():
    # la dilatacion morfologica toma el maximo: text(3) se come a comment(1)
    rgb = _rgb_con_azul([2, 2, 8, 2, 2])
    sin = decodificar_gt_diva(rgb, dilatar=False)
    con = decodificar_gt_diva(rgb, dilatar=True)
    assert sin.tolist() == [[1, 1, 3, 1, 1]]
    assert con[0, 1] == 3 and con[0, 3] == 3


def test_dtype_y_rango():
    rgb = _rgb_con_azul([8, 2, 4, 9])
    out = decodificar_gt_diva(rgb)
    assert out.dtype == np.int64
    assert out.min() >= 0 and out.max() <= 3


CODIGOS_CONOCIDOS = {2, 4, 6, 8, 10, 12}

# 14 = 8+4+2, solapamiento de las tres clases. El codigo oficial no lo mapea y
# lo degrada a fondo; se tolera porque es residual (ver el test de umbral).
CODIGOS_TOLERADOS = {14}
UMBRAL_CODIGOS_TOLERADOS = 0.01  # porcentaje de pixeles


def _distribucion(carpeta, stems=None):
    """Porcentaje de pixeles por clase sobre los GT de una carpeta."""
    from PIL import Image

    archivos = sorted(carpeta.glob("*.png"))
    if stems is not None:
        archivos = [p for p in archivos if p.stem in stems]
    assert archivos, f"sin GT en {carpeta}"

    conteo = np.zeros(4, dtype=np.int64)
    for p in archivos:
        m = decodificar_gt_diva(np.array(Image.open(p).convert("RGB")))
        conteo += np.bincount(m.ravel(), minlength=4)
    return 100.0 * conteo / conteo.sum()


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_no_hay_codigos_de_clase_sin_mapear(diva_disponible, manuscrito):
    """El test fuerte de la decodificacion: todo valor del canal azul cae en
    un codigo conocido. Un codigo sin mapear se degradaria silenciosamente a
    fondo e inflaria esa clase sin que nada avise."""
    from PIL import Image

    carpeta = diva_disponible / manuscrito / f"pixel-level-gt-{manuscrito}" / "training"
    for p in sorted(carpeta.glob("*.png")):
        azul = np.array(Image.open(p).convert("RGB"))[:, :, 2]
        pares = {int(v) for v in np.unique(azul) if v % 2 == 0}
        desconocidos = pares - CODIGOS_CONOCIDOS - CODIGOS_TOLERADOS
        assert not desconocidos, (
            f"{p.name}: codigos de canal azul sin mapear {desconocidos}"
        )


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_los_codigos_tolerados_siguen_siendo_residuales(diva_disponible, manuscrito):
    """El 14 se degrada a fondo como en el codigo oficial. Es aceptable solo
    mientras sea despreciable: si alguna vez crece, hay que mapearlo."""
    from PIL import Image

    carpeta = diva_disponible / manuscrito / f"pixel-level-gt-{manuscrito}" / "training"
    for p in sorted(carpeta.glob("*.png")):
        azul = np.array(Image.open(p).convert("RGB"))[:, :, 2]
        presentes = np.isin(azul, list(CODIGOS_TOLERADOS))
        pct = 100.0 * presentes.sum() / azul.size
        assert pct < UMBRAL_CODIGOS_TOLERADOS, (
            f"{p.name}: codigos tolerados ocupan {pct:.4f}% (umbral "
            f"{UMBRAL_CODIGOS_TOLERADOS}%) -- ya no son residuales"
        )


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_las_cuatro_clases_estan_presentes_y_el_fondo_domina(
    diva_disponible, manuscrito
):
    carpeta = diva_disponible / manuscrito / f"pixel-level-gt-{manuscrito}" / "training"
    pct = _distribucion(carpeta)
    assert (pct > 0).all(), f"{manuscrito}: alguna clase quedo vacia -> {pct}"
    assert pct[0] == pct.max(), f"{manuscrito}: el fondo deberia dominar -> {pct}"


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_decoration_es_la_clase_minoritaria(diva_disponible, manuscrito):
    """Coincide con los pesos publicados, donde decoration es la clase mas
    rara de los tres manuscritos (0.55 / 1.47 / 1.83 %)."""
    pct = _distribucion(
        diva_disponible / manuscrito / f"pixel-level-gt-{manuscrito}" / "training"
    )
    assert pct[2] == pct.min(), f"{manuscrito}: decoration no es la minoritaria -> {pct}"


def test_en_cs863_predomina_el_texto_sobre_el_comentario(diva_disponible):
    """CS863 es el unico manuscrito donde el publicado separa text (14%) de
    comment (6.35%) con holgura; sirve como control del mapeo 8/10 -> text."""
    pct = _distribucion(
        diva_disponible / "CS863" / "pixel-level-gt-CS863" / "training"
    )
    assert pct[3] > 2 * pct[1], f"CS863: text={pct[3]:.2f} comment={pct[1]:.2f}"
