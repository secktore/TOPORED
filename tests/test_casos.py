"""Casos del plan de pruebas (sección 15)."""
from pathlib import Path

import pytest

from topored.analisis import analizar
from topored.condiciones import Escenario
from topored.modelo import ErrorEntrada, cargar_json, cargar_red

EJ = Path(__file__).parent.parent / "ejemplos"


def red(disp, enl):
    return cargar_red({"dispositivos": [{"id": i, "tipo": t} for i, t in disp],
                       "enlaces": [{"a": a, "b": b} for a, b in enl]})


def cond(r, cid):
    return next(c for c in r.condiciones if c.id == cid)


def test_estrella_identifica_centro_y_hojas():
    r = analizar(red([("S1", "switch"), ("PC1", "pc"), ("PC2", "pc"), ("SRV1", "servidor")],
                     [("S1", "PC1"), ("S1", "PC2"), ("S1", "SRV1")]))
    assert r.reconocimiento.categoria == "estrella"
    assert r.reconocimiento.evidencia["centro"] == "S1"
    assert r.reconocimiento.evidencia["hojas"] == ["PC1", "PC2", "SRV1"]


def test_cadena_identifica_extremos_y_secuencia():
    r, _ = cargar_json(EJ / "cadena.json")
    res = analizar(r)
    assert res.reconocimiento.categoria == "cadena"
    assert res.reconocimiento.evidencia["extremos"] == ["PC1", "R1"]
    assert len(res.reconocimiento.evidencia["secuencia"]) == 4


def test_dos_nodos_es_cadena_por_convencion():
    assert analizar(red([("PC1", "pc"), ("PC2", "pc")], [("PC1", "PC2")])).reconocimiento.categoria == "cadena"


def test_arbol_ramificado():
    r, esc = cargar_json(EJ / "arbol_jerarquico.json")
    res = analizar(r, Escenario.desde_dict(esc))
    assert res.reconocimiento.categoria == "árbol"
    assert res.reconocimiento.evidencia["raiz"] == "R1"
    assert res.cumple_todo


def test_escenario_referencia_es_estrella_y_arbol():
    # R1 cuelga de S1 como una hoja más: S1 tiene grado n-1 => estrella (prioridad sobre árbol)
    r, esc = cargar_json(EJ / "estrella_con_router.json")
    res = analizar(r, Escenario.desde_dict(esc))
    assert res.reconocimiento.categoria == "estrella"
    assert res.reconocimiento.evidencia["centro"] == "S1"
    assert any("árbol" in x for x in res.reconocimiento.propiedades_extra)
    assert res.cumple_todo


def test_lan_sin_router_no_incumple_por_eso():
    res = analizar(red([("S1", "switch"), ("PC1", "pc"), ("PC2", "pc")],
                       [("S1", "PC1"), ("S1", "PC2")]), Escenario("red_local"))
    assert res.cumple_todo
    assert all(c.id != "C-RTR" for c in res.condiciones)


def test_salida_sin_router_incumple():
    res = analizar(red([("S1", "switch"), ("PC1", "pc"), ("PC2", "pc")],
                       [("S1", "PC1"), ("S1", "PC2")]), Escenario("red_con_salida"))
    assert not cond(res, "C-RTR").cumple


def test_nodo_aislado_se_reporta():
    r, esc = cargar_json(EJ / "nodo_aislado.json")
    res = analizar(r, Escenario.desde_dict(esc))
    assert res.propiedades.aislados == ["AP1"]
    assert not cond(res, "C-CON").cumple
    assert "AP1" in cond(res, "C-CON").nodos


def test_ciclo_bajo_condicion_de_arbol():
    r, esc = cargar_json(EJ / "arbol_con_ciclo.json")
    res = analizar(r, Escenario.desde_dict(esc))
    c = cond(res, "C-ARB")
    assert not c.cumple and "ciclo" in c.detalle
    assert {"S1", "S2", "S3"} <= set(c.nodos)


def test_identificador_repetido_se_rechaza():
    with pytest.raises(ErrorEntrada) as e:
        red([("PC1", "pc"), ("PC1", "pc")], [])
    assert any("repetido" in x for x in e.value.errores)


def test_extremo_inexistente_se_rechaza():
    with pytest.raises(ErrorEntrada) as e:
        red([("S1", "switch"), ("PC1", "pc")], [("S1", "PC9")])
    assert any("PC9" in x for x in e.value.errores)


def test_tipo_no_admitido_se_rechaza():
    with pytest.raises(ErrorEntrada):
        red([("X1", "impresora"), ("PC1", "pc")], [])


def test_fuera_de_catalogo_no_clasificada():
    # anillo de 4 nodos: ni cadena, ni estrella, ni árbol
    res = analizar(red([("S1", "switch"), ("S2", "switch"), ("S3", "switch"), ("S4", "switch")],
                       [("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S4", "S1")]),
                   Escenario("red_local"))
    assert res.reconocimiento.categoria == "no clasificada"
    assert res.cumple_todo  # no clasificada no implica incumplimiento
