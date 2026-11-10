"""TopoRed de escritorio: ejecutar desde la carpeta exterior del proyecto.
Reutiliza el paquete topored existente. No importa pandas, Streamlit ni Matplotlib.
"""
import json
import math
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

from topored.modelo import cargar_json, ErrorEntrada
from topored.analisis import analizar
from topored.condiciones import Escenario
from topored.reporte import generar_reporte


EJEMPLO = {
    "nombre": "Estrella con router",
    "dispositivos": [
        {"id": "S1", "tipo": "switch"},
        {"id": "R1", "tipo": "router"},
        {"id": "PC1", "tipo": "pc"},
        {"id": "PC2", "tipo": "pc"},
        {"id": "SRV1", "tipo": "servidor"},
    ],
    "enlaces": [
        {"a": "S1", "b": "R1"}, {"a": "S1", "b": "PC1"},
        {"a": "S1", "b": "PC2"}, {"a": "S1", "b": "SRV1"},
    ],
    "escenario": {"nombre": "red_con_salida", "exigir_conexa": True},
}
COLORES = {"router": "#c45b27", "switch": "#215da8", "pc": "#218359",
           "servidor": "#8148a3", "ap": "#00838f"}


class TopoRed(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TopoRed - Edicion de escritorio")
        self.geometry("1180x800")
        self.minsize(880, 620)
        self.resultado = None
        self.reporte = ""
        self.escenario = tk.StringVar(value="red_local")
        self.conexa = tk.BooleanVar(value=True)
        self.arbol = tk.BooleanVar(value=False)
        self.tipos_salida = ["pc", "servidor"]
        self.estado = tk.StringVar(value="Carga una red y presiona Analizar.")
        self.resumen = tk.StringVar(value="Sin resultado")
        self._interfaz()
        self.cargar_ejemplo()
        for variable in (self.escenario, self.conexa, self.arbol):
            variable.trace_add("write", self.invalidar)

    def _interfaz(self):
        barra = ttk.Frame(self, padding=10)
        barra.pack(fill="x")
        ttk.Label(barra, text="TopoRed", font=("Segoe UI", 20, "bold")).pack(side="left", padx=(0, 20))
        for texto, comando in (("Abrir JSON", self.abrir), ("Ejemplo", self.cargar_ejemplo),
                               ("Analizar", self.ejecutar), ("Guardar JSON", self.guardar_json)):
            ttk.Button(barra, text=texto, command=comando).pack(side="left", padx=4)
        self.boton_reporte = ttk.Button(barra, text="Guardar reporte TXT", command=self.guardar_reporte, state="disabled")
        self.boton_reporte.pack(side="left", padx=4)
        opciones = ttk.Frame(self, padding=(10, 0, 10, 10))
        opciones.pack(fill="x")
        ttk.Label(opciones, text="Escenario:").pack(side="left", padx=4)
        ttk.Combobox(opciones, textvariable=self.escenario, state="readonly", width=20,
                     values=("red_local", "red_con_salida")).pack(side="left", padx=4)
        ttk.Checkbutton(opciones, text="Exigir conectividad", variable=self.conexa).pack(side="left", padx=8)
        ttk.Checkbutton(opciones, text="Exigir arbol", variable=self.arbol).pack(side="left", padx=8)
        ttk.Label(self, text="Analisis estructural: no simula trafico ni comprueba acceso real a Internet.",
                  padding=(12, 0, 10, 8)).pack(anchor="w")
        panel = ttk.Panedwindow(self, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=10)
        izquierda = ttk.Frame(panel)
        derecha = ttk.Frame(panel)
        panel.add(izquierda, weight=2)
        panel.add(derecha, weight=3)
        ttk.Label(izquierda, text="Entrada JSON editable").pack(anchor="w")
        self.editor = ScrolledText(izquierda, width=45, wrap="none", font=("Consolas", 10), undo=True)
        self.editor.pack(fill="both", expand=True, pady=6)
        self.editor.bind("<<Modified>>", self.edicion)
        ttk.Label(izquierda, text="Tipos: router, switch, pc, servidor, ap. De 2 a 50 dispositivos.", wraplength=380).pack(anchor="w")
        ttk.Label(derecha, textvariable=self.resumen, wraplength=650, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=5)
        pestanas = ttk.Notebook(derecha)
        pestanas.pack(fill="both", expand=True)
        vista = ttk.Frame(pestanas)
        texto = ttk.Frame(pestanas)
        pestanas.add(vista, text="Diagrama")
        pestanas.add(texto, text="Reporte")
        self.canvas = tk.Canvas(vista, background="#f5f8fc", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.dibujar())
        self.salida = ScrolledText(texto, wrap="word", font=("Consolas", 10), state="disabled")
        self.salida.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.estado, padding=10, wraplength=1100).pack(fill="x")

    def escribir_reporte(self, texto):
        self.salida.configure(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", texto)
        self.salida.configure(state="disabled")

    def invalidar(self, *args):
        self.resultado = None
        self.reporte = ""
        self.resumen.set("Datos o escenario cambiados: presiona Analizar.")
        self.boton_reporte.configure(state="disabled")
        self.canvas.delete("all")
        self.escribir_reporte("")

    def edicion(self, event=None):
        if self.editor.edit_modified():
            self.invalidar()
            self.editor.edit_modified(False)

    def poner_datos(self, datos):
        esc = datos.get("escenario") or {}
        if not isinstance(esc, dict):
            raise ValueError("escenario debe ser un objeto JSON.")
        e = Escenario.desde_dict(esc)
        if any(tipo not in COLORES for tipo in e.tipos_con_salida):
            raise ValueError("Tipos de salida desconocidos en escenario.")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", json.dumps(datos, ensure_ascii=False, indent=2))
        self.escenario.set(e.nombre)
        self.conexa.set(e.exigir_conexa)
        self.arbol.set(e.exigir_arbol)
        self.tipos_salida = e.tipos_con_salida
        self.invalidar()
        self.editor.edit_modified(False)

    def cargar_ejemplo(self):
        self.poner_datos(EJEMPLO)
        self.estado.set("Ejemplo cargado. Presiona Analizar.")

    def abrir(self):
        ruta = filedialog.askopenfilename(title="Selecciona una red", filetypes=[("JSON", "*.json")])
        if not ruta:
            return
        try:
            p = Path(ruta)
            if p.stat().st_size > 200_000:
                raise ValueError("El archivo supera 200 000 bytes.")
            crudo = p.read_bytes()
            cargar_json(crudo)
            self.poner_datos(json.loads(crudo.decode("utf-8")))
            self.estado.set("Archivo cargado: " + p.name + ". Presiona Analizar.")
        except (OSError, ValueError, TypeError, ErrorEntrada) as exc:
            messagebox.showerror("No se pudo cargar", str(exc))

    def esc_actual(self):
        return Escenario(nombre=self.escenario.get(), exigir_conexa=self.conexa.get(),
                         exigir_arbol=self.arbol.get(), tipos_con_salida=self.tipos_salida)

    def ejecutar(self):
        self.invalidar()
        try:
            crudo = self.editor.get("1.0", "end-1c").encode("utf-8")
            red, _ = cargar_json(crudo)
            esc = self.esc_actual()
            inicio = time.perf_counter()
            r = analizar(red, esc)
            ms = (time.perf_counter() - inicio) * 1000
            self.reporte = generar_reporte(r) + f"\n\nTiempo de analisis: {ms:.3f} ms (sin validacion, dibujo ni interaccion)."
            self.resultado = r
            self.resumen.set(f"{r.reconocimiento.categoria.upper()} | {r.reconocimiento.regla} | "
                             f"{r.propiedades.num_dispositivos} dispositivos | Condiciones: "
                             + ("cumple" if r.cumple_todo else "no cumple"))
            self.escribir_reporte(self.reporte)
            self.boton_reporte.configure(state="normal")
            self.dibujar()
            self.estado.set("Analisis terminado. Revisa las pestanas Diagrama y Reporte.")
        except Exception as exc:
            self.invalidar()
            self.estado.set("No se pudo analizar la entrada.")
            self.escribir_reporte(str(exc))
            messagebox.showerror("Error de entrada o analisis", str(exc))

    def dibujar(self):
        self.canvas.delete("all")
        if self.resultado is None:
            return
        g = self.resultado.grafo
        ids = list(g.nodes)
        w, h = max(self.canvas.winfo_width(), 250), max(self.canvas.winfo_height(), 250)
        cx, cy = w / 2, h / 2
        rx, ry = max(50, w / 2 - 85), max(50, h / 2 - 90)
        posiciones = {n: (cx + rx * math.cos(2 * math.pi * i / len(ids) - math.pi / 2),
                          cy + ry * math.sin(2 * math.pi * i / len(ids) - math.pi / 2))
                      for i, n in enumerate(ids)}
        for a, b in g.edges:
            self.canvas.create_line(*posiciones[a], *posiciones[b], fill="#90a4b8", width=2)
        malos = {n for c in self.resultado.condiciones if not c.cumple for n in c.nodos}
        radio = 18 if len(ids) < 25 else 10
        for n in ids:
            x, y = posiciones[n]
            tipo = g.nodes[n]["tipo"]
            self.canvas.create_oval(x-radio, y-radio, x+radio, y+radio, fill=COLORES[tipo],
                                    outline="#b00020" if n in malos else "white", width=3)
            self.canvas.create_text(x, y+radio+13, text=n, font=("Segoe UI", 9))
            self.canvas.create_text(x, y+radio+27, text=tipo, fill="#475569", font=("Segoe UI", 8))
        self.canvas.create_text(w/2, 15, text="Distribucion circular descriptiva; no representa ubicacion fisica.",
                                width=w-20, fill="#475569", font=("Segoe UI", 9))

    def guardar_json(self):
        try:
            crudo = self.editor.get("1.0", "end-1c").encode("utf-8")
            cargar_json(crudo)
            datos = json.loads(crudo.decode("utf-8"))
            esc = self.esc_actual()
            datos["escenario"] = dict(nombre=esc.nombre, exigir_conexa=esc.exigir_conexa,
                                      exigir_arbol=esc.exigir_arbol, tipos_con_salida=esc.tipos_con_salida)
            ruta = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if ruta:
                Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, ValueError, ErrorEntrada) as exc:
            messagebox.showerror("No se pudo guardar", str(exc))

    def guardar_reporte(self):
        if not self.reporte:
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
        if ruta:
            try:
                Path(ruta).write_text(self.reporte, encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("No se pudo guardar", str(exc))


if __name__ == "__main__":
    TopoRed().mainloop()
