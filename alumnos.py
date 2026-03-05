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
    
    # --- 4. LA MAGIA: AGRUPAR LOS CURSOS ---
    def agrupar_curso(curso):
        c = str(curso).upper()
        if '1ERO' in c or '1ER' in c or '1º' in c: return '1er Año'
        if '2DO' in c or '2º' in c: return '2do Año'
        if '3ERO' in c or '3ER' in c or '3º' in c: return '3er Año'
        if '4TO' in c or '4º' in c: return '4to Año'
        if '5TO' in c or '5º' in c: return '5to Año'
        if '6TO' in c or '6º' in c: return '6to Año'
        return c.title() 
        
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
        df['ORDEN_BLOQUE'] = pd.to_numeric(df['BLOQUE'], errors='coerce').fillna(99)
        
    # 7. Filtro final de seguridad
    df = df[~df['DIA'].isin(["NAN", "", "NAT", "NONE"])]
    df = df[~df['CURSOS_AGRUPADOS'].isin(["NAN", "Nan", "", "Nat", "None"])]
        
    return df

try:
    # Cargamos los datos
    df = cargar_datos()
    
    # --- MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

    # --- LÓGICA DE INTERFAZ ---
    st.subheader("🔍 Buscador de Clases")
    
    # Usamos 3 columnas para los 3 desplegables
    col1, col2, col3 = st.columns(3)
    
    # 1. Desplegable CURSO
    lista_cursos = ["--- Seleccionar Año ---"] + sorted(df['CURSOS_AGRUPADOS'].dropna().unique().tolist())
    curso_elegido = col1.selectbox("🎓 Año:", lista_cursos)
    
    # 2. Desplegable DÍA
    dias_disponibles = df.sort_values('ORDEN_DIA')['DIA'].dropna().unique().tolist()
    dia_elegido = col2.selectbox("📅 Día:", dias_disponibles)
    
    # 3. Desplegable BLOQUE
    bloques_disponibles = df.sort_values('ORDEN_BLOQUE')['BLOQUE'].dropna().unique().tolist()
    bloque_elegido = col3.selectbox("⏰ Bloque:", bloques_disponibles)

    st.divider()

    # --- LÓGICA DE MOSTRADO ---
    if curso_elegido == "--- Seleccionar Año ---":
        st.info("👆 Por favor, selecciona un Año en el menú para ver qué clases tocan.")
    else:
        # Filtramos por los 3 campos a la vez
        filtro = (df['CURSOS_AGRUPADOS'] == curso_elegido) & (df['DIA'] == dia_elegido) & (df['BLOQUE'] == bloque_elegido)
        resultado = df[filtro]

        if not resultado.empty:
            st.success(f"✅ Clases de **{curso_elegido}** el **{dia_elegido}** (Bloque **{bloque_elegido}**):")
            
            # Solo traemos las 3 columnas pedidas y mostramos TODOS los renglones
            cols_mostrar = [c for c in ['MATERIA', 'DOCENTES', 'ESPACIOS'] if c in resultado.columns]
            
            st.dataframe(resultado[cols_mostrar], hide_index=True, use_container_width=True)
        else:
            st.info(f"☕ No hay clases registradas para **{curso_elegido}** el **{dia_elegido}** en el bloque **{bloque_elegido}**.")

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
