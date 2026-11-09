"""Flujo general (sección 12.1): entrada → validación → grafo → reconocimiento → condiciones."""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from .condiciones import Escenario, ResultadoCondicion, evaluar
from .grafo import construir_grafo
from .modelo import Red
from .reconocimiento import Propiedades, Reconocimiento, calcular_propiedades, reconocer


@dataclass
class Resultado:
    red: Red
    escenario: Escenario
    grafo: nx.Graph
    propiedades: Propiedades
    reconocimiento: Reconocimiento
    condiciones: list[ResultadoCondicion]

    @property
    def cumple_todo(self) -> bool:
        return all(c.cumple for c in self.condiciones)


def analizar(red: Red, escenario: Escenario | None = None) -> Resultado:
    escenario = escenario or Escenario()
    g = construir_grafo(red)
    p = calcular_propiedades(g)
    return Resultado(red, escenario, g, p, reconocer(g, p), evaluar(g, p, escenario))
