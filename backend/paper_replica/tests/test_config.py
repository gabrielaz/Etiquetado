import importlib
from pathlib import Path

from paper_replica.config import Config


def test_diva_root_por_defecto_cuelga_del_repo(monkeypatch):
    import paper_replica.config as mod

    monkeypatch.delenv("DIVA_ROOT", raising=False)
    recargado = importlib.reload(mod)
    assert recargado.DIVA_ROOT.name == "fewshot_data"
    assert recargado.DIVA_ROOT.parent.name == "datos-diva"


def test_diva_root_se_puede_sobreescribir_por_entorno(monkeypatch, tmp_path):
    """Colab clona el repo y los datos en directorios hermanos, no anidados."""
    import paper_replica.config as mod

    monkeypatch.setenv("DIVA_ROOT", str(tmp_path / "otro" / "fewshot_data"))
    recargado = importlib.reload(mod)
    assert recargado.DIVA_ROOT == Path(tmp_path / "otro" / "fewshot_data")

    monkeypatch.delenv("DIVA_ROOT", raising=False)
    importlib.reload(mod)


def test_config_grid_derives_from_patch_size():
    c = Config()
    assert c.img_w == 1344
    assert c.img_h == 2016
    assert c.patch_size == 336
    # la grilla debe cubrir la pagina exacta, sin resto
    assert c.img_w % c.patch_size == 0
    assert c.img_h % c.patch_size == 0
    assert c.grid_cols == 4
    assert c.grid_rows == 6
    assert c.patches_per_page == 24
    assert c.patches_per_page + c.n_crops == 34


def test_config_official_hyperparameters():
    c = Config()
    assert c.backbone == "resnet50"
    assert c.encoder_weights is None
    assert c.n_classes == 4
    assert c.lr == 0.001
    assert c.weight_decay == 0.00001
    assert c.epochs == 200
    assert c.patience == 20
    assert c.min_epochs == 50
    assert c.use_amp is False
