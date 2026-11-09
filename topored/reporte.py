"""Reporte explicativo en cuatro bloques (sección 8.4 y 12.3)."""
from __future__ import annotations

from .analisis import Resultado
from .condiciones import ESCENARIOS

LIMITACIONES = [
    "Un camino indica una secuencia de enlaces registrados, no comunicación efectiva.",
    "La presencia de un router no comprueba acceso a Internet.",
    "La ausencia de ciclos no implica que la red esté correctamente configurada.",
    "Un nodo aislado indica que no se registraron enlaces, no que el equipo esté averiado.",
    "No se analizan direccionamiento IP, VLAN, ACL, protocolos ni cobertura inalámbrica.",
]


def generar_reporte(r: Resultado) -> str:
    p, rec, esc = r.propiedades, r.reconocimiento, r.escenario
    L: list[str] = []
    L.append(f"REPORTE DE ANÁLISIS ESTRUCTURAL — {r.red.nombre}")
    L.append("=" * 60)
    L.append(f"Escenario: {ESCENARIOS[esc.nombre]}")
    L.append("")
    L.append("1. INTEGRIDAD")
    L.append(f"   Datos válidos. Dispositivos: {p.num_dispositivos} | Enlaces: {p.num_enlaces}")
    tipos: dict[str, int] = {}
    for d in r.red.dispositivos:
        tipos[d.tipo] = tipos.get(d.tipo, 0) + 1
    L.append("   Tipos: " + ", ".join(f"{t}={n}" for t, n in sorted(tipos.items())))
    L.append("")
    L.append("2. RECONOCIMIENTO")
    L.append(f"   Categoría principal: {rec.categoria.upper()}  (regla {rec.regla})")
    L.append(f"   Explicación: {rec.explicacion}")
    for k, v in rec.evidencia.items():
        L.append(f"   - {k}: {v}")
    for extra in rec.propiedades_extra:
        L.append(f"   * {extra}")
    L.append(f"   Grados: " + ", ".join(f"{n}={k}" for n, k in p.grados.items()))
    L.append(f"   Componentes: {len(p.componentes)} | Aislados: {p.aislados or 'ninguno'} | "
             f"Ciclos: {len(p.ciclos)}")
    L.append("")
    L.append("3. CUMPLIMIENTO")
    if not r.condiciones:
        L.append("   No se seleccionaron condiciones.")
    for c in r.condiciones:
        marca = "   CUMPLE" if c.cumple else "NO CUMPLE"
        L.append(f"   [{marca}] {c.id} {c.descripcion}: {c.detalle}")
    L.append(f"   Resultado global: {'cumple todas las condiciones' if r.cumple_todo else 'hay condiciones incumplidas'}")
    L.append("")
    L.append("4. OBSERVACIONES Y LÍMITES")
    if p.aislados:
        L.append(f"   - Revisar dispositivos sin enlaces registrados: {', '.join(p.aislados)}.")
    if rec.categoria == "no clasificada":
        L.append("   - La estructura está fuera del catálogo inicial; no se considera incorrecta por ello.")
    for lim in LIMITACIONES:
        L.append(f"   - {lim}")
    return "\n".join(L)
