import numpy as np
import torch

from paper_replica.config import Config
from paper_replica.losses import crear_ce_ponderada
from paper_replica.model import crear_modelo
from paper_replica.train import debe_cortar


def test_no_corta_antes_del_minimo_de_epocas():
    """El oficial exige epoca > 50 aunque no haya mejora."""
    cfg = Config()
    assert not debe_cortar(epoca=40, ultima_mejora=0, cfg=cfg)


def test_corta_tras_la_paciencia_pasado_el_minimo():
    cfg = Config()
    assert debe_cortar(epoca=80, ultima_mejora=55, cfg=cfg)


def test_no_corta_si_hubo_mejora_reciente():
    cfg = Config()
    assert not debe_cortar(epoca=80, ultima_mejora=70, cfg=cfg)


def test_overfit_a_un_parche_baja_la_loss():
    """Si esto no baja, el bug esta en el loop, no en los datos ni en el GT.
    Es el test que faltaba en el intento anterior."""
    torch.manual_seed(0)
    cfg = Config(patch_size=64)
    model = crear_modelo(cfg)
    loss_fn = crear_ce_ponderada("CB55")
    optim = torch.optim.Adam(
        model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
    )

    x = torch.rand(2, 3, 64, 64)
    y = torch.zeros(2, 64, 64, dtype=torch.long)
    y[:, 20:40, 20:40] = 3

    model.train()
    inicial = None
    for _ in range(30):
        optim.zero_grad()
        out = model(x)
        loss = loss_fn(out, y)
        loss.backward()
        optim.step()
        if inicial is None:
            inicial = loss.item()

    assert loss.item() < 0.5 * inicial, f"{inicial:.4f} -> {loss.item():.4f}"


def test_los_logits_no_explotan_durante_el_entrenamiento():
    """El bug historico aparecia despues de varios pasos, no en la init."""
    torch.manual_seed(0)
    cfg = Config(patch_size=64)
    model = crear_modelo(cfg)
    loss_fn = crear_ce_ponderada("CB55")
    optim = torch.optim.Adam(model.parameters(), lr=cfg.lr)

    x = torch.rand(4, 3, 64, 64)
    y = torch.randint(0, 4, (4, 64, 64))

    model.train()
    for _ in range(20):
        optim.zero_grad()
        out = model(x)
        assert torch.isfinite(out).all(), "logits no finitos"
        assert out.abs().max() < 1e3, f"logits explotaron: {out.abs().max():.2e}"
        loss_fn(out, y).backward()
        optim.step()


def test_entrenamiento_corto_end_to_end(diva_disponible):
    """Dos epocas reales sobre CB55: verifica que las piezas encajan."""
    from paper_replica.train import entrenar

    cfg = Config()
    res = entrenar("CB55", cfg, device="cpu", max_epochs=2)
    assert len(res["historial"]) == 2
    assert all(np.isfinite(h["val_loss"]) for h in res["historial"])
    assert res["mejor_epoca"] in (0, 1)
