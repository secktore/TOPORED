"""Uso: python -m topored ejemplos/estrella.json [--escenario red_con_salida] [--arbol] [--png salida.png]"""
import argparse
import sys

from .analisis import analizar
from .condiciones import ESCENARIOS, Escenario
from .modelo import ErrorEntrada, cargar_json
from .reporte import generar_reporte


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="topored", description="Análisis estructural de topologías de red")
    ap.add_argument("archivo", help="Archivo JSON con dispositivos y enlaces")
    ap.add_argument("--escenario", choices=list(ESCENARIOS), help="Sobrescribe el escenario del archivo")
    ap.add_argument("--arbol", action="store_true", help="Exigir organización de árbol")
    ap.add_argument("--png", help="Guardar diagrama en esta ruta")
    args = ap.parse_args(argv)
    try:
        red, esc_datos = cargar_json(args.archivo)
        if args.escenario:
            esc_datos["nombre"] = args.escenario
        if args.arbol:
            esc_datos["exigir_arbol"] = True
        resultado = analizar(red, Escenario.desde_dict(esc_datos))
    except ErrorEntrada as e:
        print("ENTRADA RECHAZADA:")
        for err in e.errores:
            print("  -", err)
        return 2
    except (OSError, ValueError) as e:
        print("Error:", e)
        return 2
    print(generar_reporte(resultado))
    if args.png:
        from .dibujo import dibujar
        dibujar(resultado, args.png)
        print(f"\nDiagrama guardado en {args.png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
