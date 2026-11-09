"""Interfaz local con Streamlit. Ejecutar: streamlit run app.py"""
import json

import pandas as pd
import streamlit as st

from topored.analisis import analizar
from topored.condiciones import ESCENARIOS, Escenario
from topored.dibujo import dibujar
from topored.modelo import TIPOS_ADMITIDOS, ErrorEntrada, cargar_json, cargar_red
from topored.reporte import generar_reporte

st.set_page_config(page_title="TopoRed", layout="wide")
st.title("TopoRed — Reconocimiento estructural de topologías")
st.caption("Análisis estructural, no operativo: no simula tráfico ni comprueba comunicación real.")

with st.sidebar:
    st.header("Escenario")
    nombre_esc = st.selectbox("Tipo", list(ESCENARIOS), format_func=ESCENARIOS.get)
    exigir_conexa = st.checkbox("Exigir una sola estructura conectada", value=True)
    exigir_arbol = st.checkbox("Exigir organización de árbol", value=False)

modo = st.radio("Entrada", ["Cargar archivo JSON", "Registro manual"], horizontal=True)
red = None
try:
    if modo == "Cargar archivo JSON":
        archivo = st.file_uploader("Archivo JSON", type="json")
        if archivo:
            red, _ = cargar_json(archivo.getvalue())
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Dispositivos")
            disp = st.data_editor(
                pd.DataFrame([{"id": "R1", "tipo": "router"}, {"id": "S1", "tipo": "switch"},
                              {"id": "PC1", "tipo": "pc"}, {"id": "PC2", "tipo": "pc"}]),
                num_rows="dynamic", key="disp",
                column_config={"tipo": st.column_config.SelectboxColumn(options=list(TIPOS_ADMITIDOS))})
        with c2:
            st.subheader("Enlaces")
            enl = st.data_editor(
                pd.DataFrame([{"a": "R1", "b": "S1"}, {"a": "S1", "b": "PC1"}, {"a": "S1", "b": "PC2"}]),
                num_rows="dynamic", key="enl")
        if st.button("Analizar", type="primary"):
            red = cargar_red({"nombre": "Registro manual",
                              "dispositivos": disp.dropna().to_dict("records"),
                              "enlaces": enl.dropna().to_dict("records")})
except ErrorEntrada as e:
    st.error("Entrada rechazada:\n\n" + "\n".join(f"- {x}" for x in e.errores))

if red:
    esc = Escenario(nombre=nombre_esc, exigir_conexa=exigir_conexa, exigir_arbol=exigir_arbol)
    r = analizar(red, esc)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Categoría", r.reconocimiento.categoria)
    m2.metric("Dispositivos", r.propiedades.num_dispositivos)
    m3.metric("Enlaces", r.propiedades.num_enlaces)
    m4.metric("Condiciones", "cumple" if r.cumple_todo else "incumple")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.pyplot(dibujar(r))
    with col_b:
        for c in r.condiciones:
            (st.success if c.cumple else st.error)(f"**{c.id} {c.descripcion}** — {c.detalle}")
        st.info(f"**Regla {r.reconocimiento.regla}:** {r.reconocimiento.explicacion}")
    texto = generar_reporte(r)
    with st.expander("Reporte completo"):
        st.code(texto, language=None)
    st.download_button("Descargar reporte (.txt)", texto, file_name="reporte_topored.txt")
