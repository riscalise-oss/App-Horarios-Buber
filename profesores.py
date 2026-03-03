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
    df = pd.read_csv(LINK_OCUPADOS)
    df.columns = [str(c).upper().strip().replace('Í', 'I') for c in df.columns]
    
    if 'DIA' in df.columns:
        df['DIA'] = df['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIÉRCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df['ORDEN_DIA'] = df['DIA'].map(orden_dias)

    if 'BLOQUE' in df.columns:
        df['BLOQUE'] = df['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        # Creamos una columna numérica oculta para ordenar cronológicamente
        df['ORDEN_BLOQUE'] = pd.to_numeric(df['BLOQUE'], errors='coerce').fillna(99)
        
    if 'DOCENTES' in df.columns:
        df['DOCENTES'] = df['DOCENTES'].astype(str).str.strip().str.upper()
        
    if 'ESPACIOS' in df.columns:
        df['ESPACIOS'] = df['ESPACIOS'].astype(str).str.strip().str.upper()
        
    return df

try:
    df = cargar_datos()
    
    # --- MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

    # --- LÓGICA DE INTERFAZ ---
    st.subheader("🔍 Buscador de Clases Asignadas")
    
    lista_docentes = sorted([d for d in df['DOCENTES'].unique() if d not in ["NAN", ""]])
    
    # Ahora usamos 2 columnas en lugar de 3 para que quede más limpio
    col1, col2 = st.columns(2)
    
    docente_elegido = col1.selectbox("👤 Docente:", lista_docentes)
    
    dias_disponibles = [dia for dia in df.sort_values('ORDEN_DIA')['DIA'].dropna().unique().tolist() if dia not in ["NAN", ""]]
    dia_elegido = col2.selectbox("📅 Día:", dias_disponibles)

    st.divider()

    # --- FILTRADO DE DATOS (Sin el selector de Bloque) ---
    filtro = (df['DOCENTES'] == docente_elegido) & (df['DIA'] == dia_elegido)
    # Ordenamos el resultado por el número de bloque para que aparezca cronológicamente
    resultado = df[filtro].sort_values('ORDEN_BLOQUE')

    # --- MOSTRAR RESULTADOS ---
    if not resultado.empty:
        st.success(f"✅ Cronograma de **{docente_elegido}** para el **{dia_elegido}**:")
        # Agregamos 'BLOQUE' al inicio de las columnas que se muestran
        cols_mostrar = [c for c in ['BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS'] if c in resultado.columns]
        st.dataframe(resultado[cols_mostrar], hide_index=True, use_container_width=True)
    else:
        st.info(f"☕ **{docente_elegido}** no tiene clases registradas el **{dia_elegido}**.")

except Exception as e:
    st.error(f"Error técnico: {e}")

# --- PIE DE PÁGINA "BY RICHARD" ---
st.markdown("""
    <style>
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        text-align: center; font-size: 12px; color: grey;
        padding: 10px; background-color: transparent; z-index: 100;
    }
    </style>
    <div class="footer">by Richard</div>
""", unsafe_allow_html=True)
