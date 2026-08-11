import torch

from paper_replica.model import crear_modelo, rango_logits


def test_forma_de_salida(cfg):
    m = crear_modelo(cfg)
    x = torch.rand(2, 3, cfg.patch_size, cfg.patch_size)
    with torch.no_grad():
        y = m(x)
    assert y.shape == (2, cfg.n_classes, cfg.patch_size, cfg.patch_size)


def test_encoder_sin_preentrenar(cfg):
    """Fase 1 replica el repo oficial: encoder_weights=None."""
    assert cfg.encoder_weights is None


def test_rango_de_logits_acotado(cfg):
    """El bug historico: batch chico -> BatchNorm degenera -> logits de 1e20.
    Un modelo recien inicializado nunca deberia acercarse a eso."""
    m = crear_modelo(cfg)
    x = torch.rand(4, 3, cfg.patch_size, cfg.patch_size)
    assert rango_logits(m, x) < 1e3


def test_batchnorm_queda_entrenable(cfg):
    """Prohibido congelar BN en fase 1: sin pesos preentrenados no hay
    estadisticas validas que congelar."""
    m = crear_modelo(cfg)
    m.train()
    bns = [
        mod
        for mod in m.modules()
        if isinstance(mod, torch.nn.modules.batchnorm._BatchNorm)
    ]
    assert bns, "el modelo deberia tener capas BatchNorm"
    assert all(bn.training for bn in bns)
    assert all(bn.track_running_stats for bn in bns)


def test_gradientes_fluyen(cfg):
    m = crear_modelo(cfg)
    x = torch.rand(2, 3, cfg.patch_size, cfg.patch_size)
    m(x).sum().backward()
    con_grad = [
        p for p in m.parameters() if p.grad is not None and p.grad.abs().sum() > 0
    ]
    assert len(con_grad) > 10
