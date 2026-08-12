import numpy as np
import pytest

from paper_replica.report import (
    F1_OFICIAL,
    METRICAS_OFICIALES,
    TOLERANCIA,
    imprimir_veredicto,
)


def _resultado(manuscrito, f1_weighted, **resto):
    """Forma minima de lo que devuelve evaluar_manuscrito.

    El veredicto se decide con la metrica oficial (weighted sobre las 4 clases),
    que es la que llama test.py del repo de los autores.
    """
    oficial = {
        "weighted": {
            "precision": resto.get("precision", f1_weighted),
            "recall": resto.get("recall", f1_weighted),
            "iou": resto.get("iou", f1_weighted / (2 - f1_weighted)),
            "f1": f1_weighted,
        },
        "macro": {"precision": 0.0, "recall": 0.0, "iou": 0.0, "f1": 0.0},
        "accuracy": f1_weighted,
    }
    return {"manuscrito": manuscrito, "oficial": oficial, "media_a": 0.0, "media_b": 0.0}


def test_veredicto_positivo_si_las_tres_entran_en_tolerancia(capsys):
    res = [_resultado(m, v) for m, v in F1_OFICIAL.items()]
    assert imprimir_veredicto(res) is True
    assert "FASE 1 SUPERADA" in capsys.readouterr().out


def test_veredicto_negativo_si_una_queda_fuera(capsys):
    res = [_resultado(m, v) for m, v in F1_OFICIAL.items()]
    res[1] = _resultado("CS18", 0.5)
    assert imprimir_veredicto(res) is False
    assert "NO SUPERADA" in capsys.readouterr().out


def test_el_borde_de_la_tolerancia_entra():
    res = [_resultado(m, v - TOLERANCIA) for m, v in F1_OFICIAL.items()]
    assert imprimir_veredicto(res) is True


def test_apenas_pasada_la_tolerancia_no_entra():
    res = [_resultado(m, v - TOLERANCIA - 1e-6) for m, v in F1_OFICIAL.items()]
    assert imprimir_veredicto(res) is False


def test_el_veredicto_usa_el_ponderado_y_no_las_variantes_a_b(capsys):
    """Regresion de la corrida del 2026-08-11: media_a=0.86 daba FUERA contra
    0.991 porque no eran la misma metrica. El veredicto no debe mirar A ni B."""
    res = [_resultado(m, v) for m, v in F1_OFICIAL.items()]
    for r in res:
        r["media_a"] = r["media_b"] = 0.0
    assert imprimir_veredicto(res) is True


def test_se_reportan_las_cuatro_metricas_publicadas(capsys):
    """El README publica precision, recall, IoU y F1. Reproducir solo el F1 no
    alcanza para afirmar que la agregacion es la correcta."""
    res = [_resultado(m, v) for m, v in F1_OFICIAL.items()]
    imprimir_veredicto(res)
    salida = capsys.readouterr().out
    for encabezado in ("prec", "rec", "iou", "f1"):
        assert encabezado in salida.lower()


def test_los_valores_oficiales_son_los_del_readme():
    assert F1_OFICIAL == {"CB55": 0.991, "CS18": 0.984, "CS863": 0.975}
    assert np.isclose(TOLERANCIA, 0.02)


def test_las_cuatro_metricas_del_readme_estan_completas():
    assert METRICAS_OFICIALES["CB55"] == {
        "precision": 0.991,
        "recall": 0.991,
        "iou": 0.982,
        "f1": 0.991,
    }
    assert METRICAS_OFICIALES["CS863"]["precision"] == 0.977
    assert METRICAS_OFICIALES["CS863"]["recall"] == 0.974


def test_el_f1_del_readme_es_consistente_con_su_precision_y_recall():
    """Check de que transcribimos bien la tabla: F1 = 2PR/(P+R)."""
    for m, v in METRICAS_OFICIALES.items():
        p, r = v["precision"], v["recall"]
        assert v["f1"] == pytest.approx(2 * p * r / (p + r), abs=5e-4), m
