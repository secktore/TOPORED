"""Escenarios y condiciones de diseño (RF03, RF06). Separado del reconocimiento.

Escenarios (sección 8):
  red_local       : no exige router. Opcionalmente exige una sola estructura conectada.
  red_con_salida  : exige al menos un router y caminos desde los equipos indicados hacia algún router.
Condición adicional:
  exigir_arbol    : conectividad y ausencia de ciclos.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from .reconocimiento import Propiedades

ESCENARIOS = {
    "red_local": "Red local (organización interna, sin exigir router)",
    "red_con_salida": "Red con salida declarada hacia otra red",
}


@dataclass
class Escenario:
    nombre: str = "red_local"
    exigir_conexa: bool = True
    exigir_arbol: bool = False
    tipos_con_salida: list[str] = field(default_factory=lambda: ["pc", "servidor"])

    @classmethod
    def desde_dict(cls, datos: dict) -> "Escenario":
        nombre = datos.get("nombre", "red_local")
        if nombre not in ESCENARIOS:
            raise ValueError(f"Escenario desconocido: {nombre}. Opciones: {', '.join(ESCENARIOS)}.")
        return cls(
            nombre=nombre,
            exigir_conexa=bool(datos.get("exigir_conexa", True)),
            exigir_arbol=bool(datos.get("exigir_arbol", False)),
            tipos_con_salida=list(datos.get("tipos_con_salida", ["pc", "servidor"])),
        )


@dataclass
class ResultadoCondicion:
    id: str
    descripcion: str
    cumple: bool
    detalle: str
    nodos: list[str] = field(default_factory=list)


def evaluar(g: nx.Graph, p: Propiedades, esc: Escenario) -> list[ResultadoCondicion]:
    res: list[ResultadoCondicion] = []

    if esc.exigir_conexa:
        if p.conexo:
            res.append(ResultadoCondicion("C-CON", "Una sola estructura conectada", True,
                                          "Todos los dispositivos pertenecen al mismo componente."))
        else:
            fuera = [v for comp in p.componentes[1:] for v in comp]
            res.append(ResultadoCondicion(
                "C-CON", "Una sola estructura conectada", False,
                f"Se encontraron {len(p.componentes)} componentes: "
                + " | ".join("{" + ", ".join(c) + "}" for c in p.componentes) + ".",
                nodos=fuera))

    if esc.nombre == "red_con_salida":
        routers = sorted(v for v, d in g.nodes(data=True) if d["tipo"] == "router")
        if not routers:
            res.append(ResultadoCondicion("C-RTR", "Al menos un router registrado", False,
                                          "El escenario declara salida hacia otra red, pero no hay router."))
        else:
            res.append(ResultadoCondicion("C-RTR", "Al menos un router registrado", True,
                                          f"Router(es): {', '.join(routers)}."))
            equipos = sorted(v for v, d in g.nodes(data=True) if d["tipo"] in esc.tipos_con_salida)
            sin_camino = [v for v in equipos if not any(nx.has_path(g, v, r) for r in routers)]
            if sin_camino:
                res.append(ResultadoCondicion(
                    "C-CAM", "Camino estructural de los equipos hacia un router", False,
                    f"Sin camino registrado hacia un router: {', '.join(sin_camino)}.", nodos=sin_camino))
            else:
                ejemplo = ""
                if equipos:
                    ruta = nx.shortest_path(g, equipos[0], routers[0])
                    ejemplo = f" Ejemplo: {' → '.join(ruta)}."
                res.append(ResultadoCondicion(
                    "C-CAM", "Camino estructural de los equipos hacia un router", True,
                    f"Los {len(equipos)} equipos ({', '.join(esc.tipos_con_salida)}) tienen camino.{ejemplo}"))

    if esc.exigir_arbol:
        if p.es_arbol:
            res.append(ResultadoCondicion("C-ARB", "Organización de árbol", True,
                                          "Conexa y sin ciclos."))
        else:
            motivos, nodos = [], []
            if not p.conexo:
                motivos.append("no es conexa")
            for c in p.ciclos:
                motivos.append("ciclo " + " → ".join(c + [c[0]]))
                nodos.extend(c)
            res.append(ResultadoCondicion("C-ARB", "Organización de árbol", False,
                                          "Incumple: " + "; ".join(motivos) + ". "
                                          "Un ciclo incumple esta condición, no es un diagnóstico de falla.",
                                          nodos=sorted(set(nodos))))
    return res
