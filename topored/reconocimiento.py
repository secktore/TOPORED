"""Reconocimiento estructural (RF04, RF05).

Reglas (sección 7):
  R-CAD  Cadena : conexo; n = 2 con un enlace, o exactamente 2 nodos de grado 1 y el resto de grado 2.
  R-EST  Estrella: n >= 3; un nodo central de grado n-1 y todos los demás de grado 1.
  R-ARB  Árbol  : conexo y |E| = |V| - 1 (sin ciclos).
Prioridad ante categorías superpuestas: Cadena > Estrella > Árbol general.
Si ninguna regla se cumple: "no clasificada" (no implica incumplimiento).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx


@dataclass
class Propiedades:
    num_dispositivos: int
    num_enlaces: int
    grados: dict[str, int]
    conexo: bool
    componentes: list[list[str]]
    aislados: list[str]
    ciclos: list[list[str]]
    es_arbol: bool


@dataclass
class Reconocimiento:
    categoria: str              # "cadena", "estrella", "árbol", "no clasificada"
    regla: str                  # identificador de la regla aplicada
    explicacion: str
    evidencia: dict = field(default_factory=dict)
    propiedades_extra: list[str] = field(default_factory=list)


def calcular_propiedades(g: nx.Graph) -> Propiedades:
    componentes = [sorted(c) for c in nx.connected_components(g)]
    componentes.sort(key=lambda c: (-len(c), c))
    conexo = len(componentes) == 1
    return Propiedades(
        num_dispositivos=g.number_of_nodes(),
        num_enlaces=g.number_of_edges(),
        grados=dict(sorted(g.degree())),
        conexo=conexo,
        componentes=componentes,
        aislados=sorted(nx.isolates(g)),
        ciclos=[c for c in nx.cycle_basis(g)],
        es_arbol=conexo and g.number_of_edges() == g.number_of_nodes() - 1,
    )


def _regla_cadena(g: nx.Graph, p: Propiedades) -> Reconocimiento | None:
    if not p.conexo:
        return None
    n = p.num_dispositivos
    grados = p.grados
    extremos = sorted(v for v, k in grados.items() if k == 1)
    if n == 2 and p.num_enlaces == 1:
        orden = extremos
    elif len(extremos) == 2 and all(k == 2 for v, k in grados.items() if v not in extremos):
        orden = nx.shortest_path(g, extremos[0], extremos[1])
    else:
        return None
    return Reconocimiento(
        categoria="cadena",
        regla="R-CAD",
        explicacion=(
            f"Estructura conexa con dos extremos ({extremos[0]} y {extremos[1]}) de grado 1"
            + (" y nodos intermedios de grado 2." if n > 2 else "; con dos nodos se adopta la convención de cadena.")
        ),
        evidencia={"extremos": extremos, "secuencia": orden},
    )


def _regla_estrella(g: nx.Graph, p: Propiedades) -> Reconocimiento | None:
    n = p.num_dispositivos
    if n < 3 or not p.conexo:
        return None
    centros = [v for v, k in p.grados.items() if k == n - 1]
    if len(centros) != 1:
        return None
    centro = centros[0]
    hojas = sorted(v for v in g.nodes if v != centro)
    if not all(p.grados[h] == 1 for h in hojas):
        return None
    return Reconocimiento(
        categoria="estrella",
        regla="R-EST",
        explicacion=(
            f"{centro} ({g.nodes[centro]['tipo']}) se conecta directamente con los {n - 1} "
            f"dispositivos restantes y cada uno de ellos tiene una sola conexión."
        ),
        evidencia={"centro": centro, "tipo_centro": g.nodes[centro]["tipo"], "hojas": hojas},
    )


def _elegir_raiz(g: nx.Graph) -> str:
    """Raíz descriptiva: un router si existe; si no, el nodo de mayor grado."""
    routers = sorted(v for v, d in g.nodes(data=True) if d["tipo"] == "router")
    if routers:
        return routers[0]
    return max(sorted(g.nodes), key=lambda v: g.degree(v))


def _regla_arbol(g: nx.Graph, p: Propiedades) -> Reconocimiento | None:
    if not p.es_arbol:
        return None
    raiz = _elegir_raiz(g)
    niveles: dict[int, list[str]] = {}
    for nodo, nivel in nx.single_source_shortest_path_length(g, raiz).items():
        niveles.setdefault(nivel, []).append(nodo)
    niveles = {k: sorted(v) for k, v in sorted(niveles.items())}
    hojas = sorted(v for v, k in p.grados.items() if k == 1)
    return Reconocimiento(
        categoria="árbol",
        regla="R-ARB",
        explicacion=(
            f"Estructura conexa sin ciclos: {p.num_dispositivos} dispositivos y "
            f"{p.num_enlaces} enlaces (|E| = |V| - 1). Se describe desde la raíz {raiz}; "
            "la raíz organiza la explicación y no demuestra una jerarquía operativa."
        ),
        evidencia={"raiz": raiz, "niveles": niveles, "hojas": hojas},
    )


def reconocer(g: nx.Graph, p: Propiedades | None = None) -> Reconocimiento:
    p = p or calcular_propiedades(g)
    for regla in (_regla_cadena, _regla_estrella, _regla_arbol):  # orden = prioridad
        r = regla(g, p)
        if r:
            if p.es_arbol and r.categoria != "árbol":
                r.propiedades_extra.append("También cumple las propiedades de árbol (conexo y sin ciclos).")
            return r
    motivos = []
    if not p.conexo:
        motivos.append(f"tiene {len(p.componentes)} componentes separados")
    if p.ciclos:
        motivos.append(f"contiene {len(p.ciclos)} ciclo(s) independiente(s)")
    return Reconocimiento(
        categoria="no clasificada",
        regla="SIN-REGLA",
        explicacion=(
            "La estructura no coincide con cadena, estrella ni árbol"
            + (": " + " y ".join(motivos) if motivos else "")
            + ". Esto no equivale a un incumplimiento."
        ),
        evidencia={"motivos": motivos},
    )
