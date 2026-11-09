# TopoRed — Reconocimiento sintáctico-estructural de topologías de red

Materia: Reconocimiento de Patrones Sintáctico-Estructural · CU UAEM Nezahualcóyotl · Eduardo Ruiz

Aplicación en **Python** que representa una red pequeña como un **grafo etiquetado** G = (V, E),
reconoce su estructura (cadena, estrella, árbol) mediante reglas y revisa condiciones de un escenario,
generando un diagrama y un reporte explicativo. El análisis es estructural, no operativo.

## Estado del avance (versión 0.1.0)

| Etapa del plan (sección 14) | Estado |
|---|---|
| 1. Fundamentos | Hecho (documento del proyecto) |
| 2. Reglas | Implementadas: R-CAD, R-EST, R-ARB, C-CON, C-RTR, C-CAM, C-ARB |
| 3. Datos | Esquema JSON + validación de integridad |
| 4. Entorno | `requirements.txt` y `pyproject.toml` |
| 5. Núcleo | Grafo, propiedades, reconocimiento y condiciones funcionando |
| 6. Presentación | Reporte en texto, diagrama PNG, interfaz Streamlit |
| 7. Verificación | 13 pruebas automatizadas (pytest), todas aprobadas |
| 8. Complementos | Pendiente (PDF, CSV, Excel, PyVis) |

## Flujo de la aplicación

```
Entrada (JSON o registro manual)
   ↓  modelo.py        → Pydantic revisa formato; validar_integridad() revisa reglas de datos
Revisión de datos
   ↓  grafo.py         → construye nx.Graph con atributo "tipo" en cada nodo
Construcción del grafo
   ↓  reconocimiento.py → propiedades (grados, componentes, aislados, ciclos) + reglas con prioridad
Reconocimiento estructural
   ↓  condiciones.py   → reglas del escenario, separadas del reconocimiento
Aplicación de condiciones
   ↓  reporte.py / dibujo.py / app.py
Reporte y visualización
```

## Estructura del código

```
topored/
├── app.py                  Interfaz local (Streamlit)
├── requirements.txt
├── pyproject.toml
├── topored/
│   ├── modelo.py           Vocabulario, esquemas y validación (RF01, RF02)
│   ├── grafo.py            Construcción de G = (V, E)
│   ├── reconocimiento.py   Reglas de cadena, estrella y árbol (RF04, RF05)
│   ├── condiciones.py      Escenarios y condiciones (RF03, RF06)
│   ├── analisis.py         Orquesta el flujo completo
│   ├── reporte.py          Reporte en cuatro bloques (RF07)
│   ├── dibujo.py           Diagrama con Matplotlib
│   └── __main__.py         Ejecución por consola
├── ejemplos/               Redes de prueba en JSON
└── tests/test_casos.py     Casos del plan de pruebas
```

## Reglas implementadas

Reconocimiento (prioridad: Cadena > Estrella > Árbol; si ninguna aplica → "no clasificada"):

| Regla | Condición |
|---|---|
| R-CAD Cadena | Conexa; n = 2 con un enlace, o exactamente 2 nodos de grado 1 y el resto de grado 2 |
| R-EST Estrella | n ≥ 3; un único nodo de grado n − 1 y todos los demás de grado 1 |
| R-ARB Árbol | Conexa y \|E\| = \|V\| − 1 (sin ciclos) |

Condiciones del escenario:

| Condición | Aplica en | Qué revisa |
|---|---|---|
| C-CON | Si se exige estructura conectada | Un solo componente conexo |
| C-RTR | red_con_salida | Al menos un router |
| C-CAM | red_con_salida | Camino desde cada pc/servidor hacia algún router |
| C-ARB | Si se exige árbol | Conexa y sin ciclos (reporta el ciclo encontrado) |

Validación de entrada: identificadores únicos, 5 tipos admitidos (`router`, `switch`, `pc`, `servidor`, `ap`),
entre 2 y 50 dispositivos, extremos existentes, sin bucles ni enlaces paralelos, archivo ≤ 200 KB.

## Formato de entrada (JSON)

```json
{
  "nombre": "Escenario de referencia",
  "escenario": {"nombre": "red_con_salida", "exigir_conexa": true, "exigir_arbol": false},
  "dispositivos": [
    {"id": "R1", "tipo": "router"},
    {"id": "S1", "tipo": "switch"},
    {"id": "PC1", "tipo": "pc"}
  ],
  "enlaces": [
    {"a": "R1", "b": "S1"},
    {"a": "S1", "b": "PC1"}
  ]
}
```

## Instalación y ejecución

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Consola
python -m topored ejemplos/arbol_jerarquico.json --png diagrama.png
python -m topored ejemplos/estrella.json --escenario red_con_salida
python -m topored ejemplos/arbol_con_ciclo.json --arbol

# Interfaz gráfica (se abre en el navegador)
streamlit run app.py

# Pruebas
pytest -v
```

## Casos de prueba (sección 15)

| Caso | Resultado obtenido |
|---|---|
| Estrella | Centro S1, hojas PC1, PC2, SRV1 |
| Cadena | Extremos PC1 y R1, secuencia de 4 nodos |
| Dos nodos | Cadena por convención |
| Árbol ramificado | Árbol con raíz R1, cumple condiciones |
| Escenario de referencia | Estrella (centro S1) y además propiedad de árbol |
| LAN sin router | No incumple por ese motivo |
| Salida sin router | C-RTR incumplida |
| Nodo aislado | AP1 reportado; C-CON incumplida |
| Ciclo bajo condición de árbol | C-ARB incumplida, ciclo S1 → S2 → S3 |
| Identificador repetido | Entrada rechazada |
| Extremo inexistente | Entrada rechazada |
| Tipo no admitido | Entrada rechazada |
| Fuera de catálogo (anillo) | "No clasificada", sin incumplimiento |

## Siguientes pasos

1. Formalizar las reglas como gramática/notación (vocabulario, relaciones, reglas de composición) para el documento.
2. Agregar ejemplos y contraejemplos por regla (p. ej. estrella con centro que no es switch).
3. Registrar tiempos de análisis con redes de 10, 25 y 50 dispositivos (sección 19).
4. Complementos: exportación PDF (ReportLab), CSV/Excel (pandas, openpyxl), vista interactiva (PyVis).
5. Documentar dependencias: versión, licencia y uso de cada una.

## Limitaciones

Un camino no implica comunicación efectiva; un router no comprueba acceso a Internet; la ausencia de ciclos
no implica configuración correcta; no se analizan IP, VLAN, ACL, protocolos ni cobertura inalámbrica.
