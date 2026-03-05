import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ámbitos Alumnos", page_icon="logo.png", layout="wide")

# --- CSS LIMPIO Y SEGURO ---
ocultar_menu = """
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
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
            <h1 style="margin: 0; padding: 0;">Ámbitos Alumnos</h1>
        </div>
    """, unsafe_allow_html=True)
except Exception:
    st.title("👨‍🎓 Ámbitos Alumnos")

# --- ENLACE A DATOS ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    # 1. Leemos el CSV
    df = pd.read_csv(LINK_OCUPADOS)
    
    # 2. Estandarizamos los nombres de las columnas
    df.columns = [str(c).upper().strip().replace('Í', 'I') for c in df.columns]
    
    # 3. Eliminamos vacíos ANTES de procesar
    columnas_clave = [col for col in ['CURSOS', 'DIA', 'BLOQUE'] if col in df.columns]
    if columnas_clave:
        df = df.dropna(subset=columnas_clave)
    
    # --- 4. LA MAGIA: AGRUPAR LOS CURSOS Y FILTRAR ---
    def agrupar_curso(curso):
        c = str(curso).upper()
        if '7MO' in c or '7º' in c: return '7mo Grado'
        if '1ERO' in c or '1ER' in c or '1º' in c: return '1er Año'
        if '2DO' in c or '2º' in c: return '2do Año'
        if '3ERO' in c or '3ER' in c or '3º' in c: return '3er Año'
        if '4TO' in c or '4º' in c: return '4to Año'
        if '5TO' in c or '5º' in c: return '5to Año'
        # Si no es de 7mo a 5to (ej. "Inicial", "Reunión", "6to"), devuelve None para borrarlo
        return None 
        
    if 'CURSOS' in df.columns:
        df['CURSOS_AGRUPADOS'] = df['CURSOS'].apply(agrupar_curso)

    # 5. Limpieza DÍA
    if 'DIA' in df.columns:
        df['DIA'] = df['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "MIÉRCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df['ORDEN_DIA'] = df['DIA'].map(orden_dias)

    # 6. Limpieza BLOQUE
    if 'BLOQUE' in df.columns:
        df['BLOQUE'] = df['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
      
