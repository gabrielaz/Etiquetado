import numpy as np

from paper_replica.report import F1_OFICIAL, TOLERANCIA, imprimir_veredicto


def _resultado(manuscrito, media_a, media_b):
    return {"manuscrito": manuscrito, "media_a": media_a, "media_b": media_b}


def test_veredicto_positivo_si_las_tres_entran_en_tolerancia(capsys):
    res = [_resultado(m, v, v) for m, v in F1_OFICIAL.items()]
    assert imprimir_veredicto(res) is True
    assert "FASE 1 SUPERADA" in capsys.readouterr().out


def test_veredicto_negativo_si_una_queda_fuera(capsys):
    res = [_resultado(m, v, v) for m, v in F1_OFICIAL.items()]
    res[1]["media_a"] = res[1]["media_b"] = 0.5
    assert imprimir_veredicto(res) is False
    assert "NO SUPERADA" in capsys.readouterr().out


def test_alcanza_con_que_una_variante_entre(capsys):
    """El criterio es reproducir el numero publicado con alguna de las dos
    lecturas del F1, no con las dos."""
    res = []
    for m, v in F1_OFICIAL.items():
        res.append(_resultado(m, 0.4, v))
    assert imprimir_veredicto(res) is True


def test_el_borde_de_la_tolerancia_entra():
    res = [_resultado(m, v - TOLERANCIA, v - TOLERANCIA) for m, v in F1_OFICIAL.items()]
    assert imprimir_veredicto(res) is True


def test_apenas_pasada_la_tolerancia_no_entra():
    res = [
        _resultado(m, v - TOLERANCIA - 1e-6, v - TOLERANCIA - 1e-6)
        for m, v in F1_OFICIAL.items()
    ]
    assert imprimir_veredicto(res) is False


def test_los_valores_oficiales_son_los_del_readme():
    assert F1_OFICIAL == {"CB55": 0.991, "CS18": 0.984, "CS863": 0.975}
    assert np.isclose(TOLERANCIA, 0.02)
