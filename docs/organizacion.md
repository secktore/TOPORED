# Organización de TopoRed

## Arquitectura actual

TopoRed es una aplicación de escritorio en Python.
La interfaz y el núcleo se ejecutan en el mismo programa.
No existe actualmente un servidor backend ni una API web.

## Interfaz: responsabilidad equivalente al frontend

Archivo principal:
- app_escritorio.py

Funciones:
- Mostrar la ventana y sus controles.
- Cargar y editar archivos JSON.
- Seleccionar el escenario.
- Mostrar el diagrama y los resultados.
- Guardar los datos y el reporte.

## Núcleo: lógica de análisis

Carpeta:
- topored/

Módulos:
- modelo.py: validación de datos.
- grafo.py: construcción del grafo.
- reconocimiento.py: reconocimiento de topologías.
- condiciones.py: evaluación de condiciones.
- analisis.py: coordinación del análisis.
- reporte.py: generación del reporte.

## Integración

Conecta la interfaz con el núcleo de análisis.

Funciones:
- Enviar los datos para su validación.
- Ejecutar el análisis.
- Mostrar resultados y errores.
- Probar el funcionamiento completo.

Full stack describe el trabajo que abarca interfaz y lógica.
No es una tercera capa ni una carpeta independiente.

## Pruebas y distribución

- tests/: pruebas automatizadas del núcleo.
- ejemplos/: archivos para comprobar el análisis.
- construir_escritorio.bat: empaquetado de la versión de escritorio.
- El ejecutable se distribuye con sus archivos auxiliares
  mediante un ZIP adjunto a una Release de GitHub.

## Versión HTML

La edición HTML y JavaScript es una alternativa autónoma.
No está conectada al núcleo Python.

## Flujo de trabajo en GitHub

1. Crear una rama por tarea.
2. Realizar los cambios.
3. Probarlos.
4. Guardarlos mediante un commit.
5. Abrir un pull request hacia main.
6. Revisar e integrar los cambios.
