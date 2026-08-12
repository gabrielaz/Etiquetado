"""La metrica que publica el repo oficial no es la que veniamos midiendo.

test.py de axelden/Few-shot-DIA-WACV2023 llama a get_scores(average="weighted")
sobre la concatenacion plana de TODOS los pixeles del split, con las 4 clases y
el fondo incluido. Nuestras variantes A y B promediaban macro sobre las 3 clases
de primer plano, por pagina. Son metricas distintas, no numeros en desacuerdo.

Estos tests fijan la implementacion contra sklearn, que es literalmente lo que
llaman los autores.
"""

import numpy as np
import pytest

from paper_replica.evaluate import metricas_desde_confusion, matriz_confusion

sklearn_metrics = pytest.importorskip("sklearn.metrics")


def _cm(gt, pred, n=4):
    # ojo con el orden: matriz_confusion(pred, gt, n) deja filas=gt, columnas=pred
    return matriz_confusion(np.asarray(pred), np.asarray(gt), n)


def test_prediccion_perfecta_da_uno_en_todo():
    cm = np.diag([100, 50, 10, 40])
    m = metricas_desde_confusion(cm)
    for promedio in ("weighted", "macro"):
        for metrica in ("precision", "recall", "f1", "iou"):
            assert m[promedio][metrica] == pytest.approx(1.0)
    assert m["accuracy"] == pytest.approx(1.0)


def test_paridad_exacta_con_sklearn():
    """El criterio de correccion: dar lo mismo que la funcion que llaman los
    autores. Si esto pasa, nuestro numero es comparable con el README."""
    rng = np.random.default_rng(0)
    gt = rng.integers(0, 4, size=20000)
    # prediccion correlacionada con el gt, no aleatoria: si no, todas las
    # metricas dan ~0.25 y el test no distinguiria una implementacion rota
    pred = np.where(rng.random(20000) < 0.8, gt, rng.integers(0, 4, size=20000))

    m = metricas_desde_confusion(_cm(gt, pred))

    for promedio in ("weighted", "macro"):
        esperado = {
            "precision": sklearn_metrics.precision_score,
            "recall": sklearn_metrics.recall_score,
            "f1": sklearn_metrics.f1_score,
            "iou": sklearn_metrics.jaccard_score,
        }
        for nombre, fn in esperado.items():
            assert m[promedio][nombre] == pytest.approx(
                fn(gt, pred, average=promedio, zero_division=0)
            ), f"{promedio}/{nombre}"

    assert m["accuracy"] == pytest.approx(sklearn_metrics.accuracy_score(gt, pred))


def test_paridad_con_sklearn_en_datos_desbalanceados():
    """El caso real: el fondo es ~82% de los pixeles. Es justamente donde
    weighted y macro se separan, asi que es donde un promedio mal hecho se nota."""
    rng = np.random.default_rng(1)
    gt = rng.choice([0, 1, 2, 3], size=50000, p=[0.82, 0.084, 0.006, 0.09])
    pred = np.where(rng.random(50000) < 0.9, gt, rng.integers(0, 4, size=50000))

    m = metricas_desde_confusion(_cm(gt, pred))
    for promedio in ("weighted", "macro"):
        assert m[promedio]["f1"] == pytest.approx(
            sklearn_metrics.f1_score(gt, pred, average=promedio, zero_division=0)
        )


def test_el_fondo_infla_el_ponderado_frente_al_macro():
    """Por que 0.86 y 0.991 nunca fueron comparables: con el fondo dominando y
    bien predicho, el ponderado queda muy por encima del macro sin fondo."""
    # fondo casi perfecto, decoration (clase 2, minoritaria) casi siempre mal
    cm = np.array(
        [[82000, 100, 50, 100],
         [200, 8000, 20, 150],
         [300, 50, 150, 50],
         [200, 200, 30, 8500]],
        dtype=np.int64,
    )
    m = metricas_desde_confusion(cm)
    assert m["weighted"]["f1"] > m["macro"]["f1"] + 0.1

    # y el macro sobre las 3 clases de primer plano (lo que mediamos antes)
    # queda todavia mas abajo que el macro sobre las 4
    macro_sin_fondo = float(np.mean(m["por_clase"]["f1"][1:]))
    assert macro_sin_fondo < m["macro"]["f1"]
    assert macro_sin_fondo < m["weighted"]["f1"]


def test_recall_ponderado_es_la_accuracy():
    """Identidad de sklearn: el recall ponderado por soporte es exactamente la
    accuracy. Sirve de check independiente de la implementacion."""
    rng = np.random.default_rng(2)
    gt = rng.choice([0, 1, 2, 3], size=10000, p=[0.7, 0.1, 0.05, 0.15])
    pred = np.where(rng.random(10000) < 0.85, gt, rng.integers(0, 4, size=10000))
    m = metricas_desde_confusion(_cm(gt, pred))
    assert m["weighted"]["recall"] == pytest.approx(m["accuracy"])


def test_iou_y_f1_cumplen_la_relacion_por_clase():
    """IoU = F1 / (2 - F1) para una misma clase. Es la relacion que se verifica
    en el README oficial de CB55 (F1 0.991 -> IoU 0.982)."""
    cm = np.array(
        [[900, 30, 10, 20],
         [40, 500, 10, 30],
         [10, 20, 200, 15],
         [25, 35, 5, 600]],
        dtype=np.int64,
    )
    m = metricas_desde_confusion(cm)
    for f1, iou in zip(m["por_clase"]["f1"], m["por_clase"]["iou"]):
        assert iou == pytest.approx(f1 / (2 - f1))


def test_clase_ausente_no_entra_en_el_macro():
    """sklearn promedia sobre las clases presentes en gt o en pred. Una clase
    que no aparece en ninguno no debe arrastrar el macro a cero."""
    gt = np.array([0, 0, 1, 1, 3, 3])
    pred = np.array([0, 0, 1, 1, 3, 3])
    m = metricas_desde_confusion(_cm(gt, pred))
    assert m["macro"]["f1"] == pytest.approx(1.0)
    assert m["soporte"][2] == 0


def test_la_matriz_de_confusion_alcanza_para_reconstruir_todo():
    """Consecuencia practica: guardando la matriz se puede recalcular cualquier
    agregacion despues, sin el modelo ni la GPU. Es lo que faltaba guardar."""
    rng = np.random.default_rng(3)
    gt = rng.integers(0, 4, size=5000)
    pred = np.where(rng.random(5000) < 0.75, gt, rng.integers(0, 4, size=5000))

    cm = _cm(gt, pred)
    desde_matriz = metricas_desde_confusion(cm)
    desde_json = metricas_desde_confusion(np.array(cm.tolist()))

    assert desde_matriz["weighted"]["f1"] == pytest.approx(desde_json["weighted"]["f1"])
