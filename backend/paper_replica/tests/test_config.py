from paper_replica.config import Config


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
