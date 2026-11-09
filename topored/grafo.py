"""Construcción del grafo etiquetado G = (V, E)."""
import networkx as nx

from .modelo import Red


def construir_grafo(red: Red) -> nx.Graph:
    g = nx.Graph(nombre=red.nombre)
    for d in red.dispositivos:
        g.add_node(d.id, tipo=d.tipo)
    for e in red.enlaces:
        g.add_edge(e.a, e.b)
    return g
