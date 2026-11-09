"""Modelo de datos y validación de integridad (RF01, RF02).

Primitivas del patrón: dispositivos (nodos etiquetados por tipo).
Relación: enlace no dirigido entre dos dispositivos.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

# Vocabulario de etiquetas admitidas (sección 5.2)
TIPOS_ADMITIDOS = ("router", "switch", "pc", "servidor", "ap")
TipoDispositivo = Literal["router", "switch", "pc", "servidor", "ap"]

MIN_DISPOSITIVOS = 2
MAX_DISPOSITIVOS = 50
MAX_BYTES_ARCHIVO = 200_000  # límite de tamaño de entrada (sección 18)


class Dispositivo(BaseModel):
    id: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_\-]+$")
    tipo: TipoDispositivo


class Enlace(BaseModel):
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)


class Red(BaseModel):
    nombre: str = "Red sin nombre"
    dispositivos: list[Dispositivo]
    enlaces: list[Enlace] = []


class ErrorEntrada(Exception):
    """Se lanza cuando los datos no permiten construir el modelo."""

    def __init__(self, errores: list[str]):
        self.errores = errores
        super().__init__("; ".join(errores))


def validar_integridad(red: Red) -> list[str]:
    """Revisa las reglas de integridad. Devuelve la lista de errores (vacía si es válida)."""
    errores: list[str] = []
    n = len(red.dispositivos)
    if not (MIN_DISPOSITIVOS <= n <= MAX_DISPOSITIVOS):
        errores.append(
            f"La red tiene {n} dispositivos; se admiten entre {MIN_DISPOSITIVOS} y {MAX_DISPOSITIVOS}."
        )

    vistos: set[str] = set()
    for d in red.dispositivos:
        if d.id in vistos:
            errores.append(f"Identificador repetido: {d.id}.")
        vistos.add(d.id)

    pares: set[frozenset[str]] = set()
    for i, e in enumerate(red.enlaces, start=1):
        for extremo in (e.a, e.b):
            if extremo not in vistos:
                errores.append(f"Enlace {i} ({e.a}-{e.b}): el extremo {extremo} no existe.")
        if e.a == e.b:
            errores.append(f"Enlace {i}: {e.a} no puede conectarse consigo mismo (grafo simple).")
        par = frozenset((e.a, e.b))
        if par in pares and e.a != e.b:
            errores.append(f"Enlace {i}: conexión duplicada entre {e.a} y {e.b} (enlace paralelo).")
        pares.add(par)
    return errores


def cargar_red(datos: dict) -> Red:
    """Convierte un diccionario en Red validada o lanza ErrorEntrada."""
    try:
        red = Red.model_validate(datos)
    except ValidationError as exc:
        errores = []
        for err in exc.errors():
            ruta = ".".join(str(p) for p in err["loc"])
            errores.append(f"Formato inválido en '{ruta}': {err['msg']}.")
        raise ErrorEntrada(errores) from None
    errores = validar_integridad(red)
    if errores:
        raise ErrorEntrada(errores)
    return red


def cargar_json(origen: str | Path | bytes) -> tuple[Red, dict]:
    """Lee un archivo JSON (ruta o bytes). Devuelve la red y el bloque 'escenario' si existe.

    Solo se interpreta como datos: nunca se ejecuta contenido del archivo.
    """
    if isinstance(origen, (str, Path)):
        crudo = Path(origen).read_bytes()
    else:
        crudo = origen
    if len(crudo) > MAX_BYTES_ARCHIVO:
        raise ErrorEntrada([f"El archivo supera {MAX_BYTES_ARCHIVO} bytes."])
    try:
        datos = json.loads(crudo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ErrorEntrada([f"El archivo no es JSON válido: {exc}."]) from None
    if not isinstance(datos, dict):
        raise ErrorEntrada(["El JSON debe ser un objeto con 'dispositivos' y 'enlaces'."])
    escenario = datos.pop("escenario", {}) or {}
    return cargar_red(datos), escenario
