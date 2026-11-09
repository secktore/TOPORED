"""Diagrama estático con Matplotlib. El reconocimiento no depende de este módulo."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from .analisis import Resultado

COLORES = {"router": "#d1495b", "switch": "#00798c", "pc": "#edae49",
           "servidor": "#30638e", "ap": "#7a5195"}


def _layout_jerarquico(t: nx.DiGraph, raiz: str) -> dict:
    """Coloca cada hoja en una columna y cada padre centrado sobre sus hijos (sin cruces)."""
    pos: dict = {}
    siguiente = [0]

    def colocar(n, nivel):
        hijos = sorted(t.successors(n))
        if not hijos:
            x = siguiente[0]
            siguiente[0] += 1
        else:
            xs = [colocar(h, nivel + 1) for h in hijos]
            x = sum(xs) / len(xs)
        pos[n] = (x, -nivel)
        return x

    colocar(raiz, 0)
    return pos


def _posiciones(r: Resultado) -> dict:
    g = r.grafo
    if r.reconocimiento.categoria == "cadena":
        return {n: (i, 0) for i, n in enumerate(r.reconocimiento.evidencia["secuencia"])}
    if r.propiedades.es_arbol:
        raiz = r.reconocimiento.evidencia.get("raiz") or r.reconocimiento.evidencia.get("centro")
        if raiz is None:
            raiz = max(g.nodes, key=g.degree)
        return _layout_jerarquico(nx.bfs_tree(g, raiz), raiz)
    return nx.spring_layout(g, seed=7)


def dibujar(r: Resultado, ruta: str | None = None):
    g = r.grafo
    fig, ax = plt.subplots(figsize=(7, 5))
    pos = _posiciones(r)
    malos = {n for c in r.condiciones if not c.cumple for n in c.nodos}
    colores = [COLORES[g.nodes[n]["tipo"]] for n in g.nodes]
    bordes = ["black" if n in malos else "white" for n in g.nodes]
    nx.draw_networkx_edges(g, pos, ax=ax, width=2, edge_color="#888")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colores, node_size=1300,
                           edgecolors=bordes, linewidths=3)
    nx.draw_networkx_labels(g, pos, ax=ax, font_color="white", font_size=9, font_weight="bold")
    for t, c in COLORES.items():
        ax.scatter([], [], color=c, label=t, s=100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=5, fontsize=8, frameon=False)
    ax.set_title(f"{r.red.nombre} — {r.reconocimiento.categoria}", fontsize=11)
    ax.axis("off")
    ax.margins(0.12)
    fig.tight_layout()
    if ruta:
        fig.savefig(ruta, dpi=130)
        plt.close(fig)
    return fig
