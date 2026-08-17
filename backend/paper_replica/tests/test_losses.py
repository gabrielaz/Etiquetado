import numpy as np
import pytest
import torch

from paper_replica.losses import PESOS_CE, crear_ce_ponderada


@pytest.mark.parametrize("manuscrito", ["CB55", "CS18", "CS863"])
def test_hay_un_peso_por_clase(manuscrito):
    assert PESOS_CE[manuscrito].shape == (4,)
    assert (PESOS_CE[manuscrito] > 0).all()


def test_pesos_reproducen_los_del_repo_oficial():
    esperado = np.sqrt([1.0 / 82, 1.0 / 8.36, 1.0 / 0.55, 1.0 / 8.68])
    assert np.allclose(PESOS_CE["CB55"], esperado)


def test_la_clase_rara_pesa_mas_que_el_fondo():
    # decoration (0.55% en CB55) debe pesar mucho mas que el fondo (82%)
    p = PESOS_CE["CB55"]
    assert p[2] > p[0]
    assert p[2] > p[3]


def test_prediccion_perfecta_da_loss_casi_cero():
    loss = crear_ce_ponderada("CB55")
    gt = torch.tensor([[[0, 1], [2, 3]]])
    # logits muy confiados en la clase correcta
    logits = torch.full((1, 4, 2, 2), -50.0)
    for y in range(2):
        for x in range(2):
            logits[0, gt[0, y, x], y, x] = 50.0
    assert loss(logits, gt).item() < 1e-4


def test_prediccion_pesima_da_loss_grande():
    loss = crear_ce_ponderada("CB55")
    gt = torch.zeros((1, 2, 2), dtype=torch.long)
    logits = torch.full((1, 4, 2, 2), -50.0)
    logits[:, 3] = 50.0  # predice text donde el GT dice fondo
    assert loss(logits, gt).item() > 10.0


def test_espera_logits_no_probabilidades():
    """El repo oficial aplica softmax antes de CrossEntropyLoss, que ya hace
    log-softmax. Nuestra version recibe logits crudos: pasarle probabilidades
    debe dar una loss claramente distinta."""
    loss = crear_ce_ponderada("CB55")
    gt = torch.zeros((1, 2, 2), dtype=torch.long)
    logits = torch.randn(1, 4, 2, 2) * 10
    con_logits = loss(logits, gt).item()
    con_probs = loss(torch.softmax(logits, dim=1), gt).item()
    assert abs(con_logits - con_probs) > 0.1
