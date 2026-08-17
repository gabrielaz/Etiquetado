import numpy as np
import pytest

from paper_replica.config import DIVA_ROOT, Config


@pytest.fixture
def cfg():
    return Config()


@pytest.fixture
def diva_disponible():
    if not DIVA_ROOT.exists():
        pytest.skip(f"datos DIVA no encontrados en {DIVA_ROOT}")
    return DIVA_ROOT


@pytest.fixture
def pagina_sintetica(cfg):
    """Imagen RGB uint8 con el tamano exacto de una pagina redimensionada."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (cfg.img_h, cfg.img_w, 3), dtype=np.uint8)


@pytest.fixture
def mascara_sintetica(cfg):
    """Mascara de etiquetas con las 4 clases presentes."""
    m = np.zeros((cfg.img_h, cfg.img_w), dtype=np.int64)
    m[100:800, 100:1200] = 3     # text
    m[900:1200, 100:600] = 1     # comment
    m[1500:1600, 200:300] = 2    # decoration
    return m
