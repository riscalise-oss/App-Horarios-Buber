import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ámbitos Profesores", page_icon="logo.png", layout="wide")

# --- CSS LIMPIO Y SEGURO ---
ocultar_menu = """
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    </style>
"""
st.markdown(ocultar_menu, unsafe_allow_html=True)

# --- TÍTULO CON LOGO ---
try:
    with open("logo.png", "rb") as f:
        data = f.read()
    img_base64 = base64.b64encode(data).decode()
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{img_base64}" width="70" style="margin-right: 15px; border-radius: 8px;">
            <h1 style="margin: 0; padding: 0;">Ámbitos Profesores</h1>
        </div>
    """, unsafe_allow_html=True)
except Exception:
    st.title("👨‍🏫 Ámbitos Profesores")

# --- ENLACE A DATOS ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    # 1. Leemos el CSV
    df = pd.read_csv(LINK_OCUPADOS)
    
    # 2. Estandarizamos los nombres de las columnas
    df.columns = [str(c).upper().strip().replace('Í', 'I') for c in df.columns]
    
    # 3. LA SOLUCIÓN: Eliminamos los vacíos (nulos reales) ANTES de convertir a texto
    columnas_clave = [col for col in ['DOCENTES', 'DIA'] if col in df.columns]
    if columnas_clave:
        df = df.dropna(subset=columnas_clave)
    
    # 4. Ahora sí, convertimos a texto limpio y ordenamos
    if 'DIA' in df.columns:
        df['DIA'] = df['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
        # Agregamos MIÉRCOLES con y sin tilde para que el orden sea perfecto siempre
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "MIÉRCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df['ORDEN_DIA'] = df['DIA'].map(orden_dias)

    if 'BLOQUE' in df.columns:
        df['BLOQUE'] = df['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        df['ORDEN_BLOQUE'] = pd.to_numeric(df['BLOQUE'], errors='coerce').fillna(99)
        
    if 'DOCENTES' in df.columns:
        df['DOCENTES'] = df['DOCENTES'].astype(str).str.strip().str.upper()
        
    if 'ESPACIOS' in df.columns:
        df['ESPACIOS'] = df['ESPACIOS'].astype(str).str.strip().str.upper()

    # Filtro final de seguridad por si quedó algún texto sucio
    df = df[~df['DIA
