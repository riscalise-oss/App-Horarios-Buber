import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")

st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES ---
# ⚠️ RECUERDA PEGAR TU ENLACE DE ASIGNACIONES AQUÍ:
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhgZSlV_TATdDowWFQkR-R_hK-F-OGu5dYfwfErAjbPnWsQ4jrQvgfxpQFxs73dtKalvDV1_f-Ec21/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5se3brxjtH9uEkXNlt03sha1MqpIwWYCbMH29Sz-Bsxz8R1PHcuPPJ-ERLQuEuC7wPP8fzIkOBVG/pub?gid=447717872&single=true&output=csv"

# --- 2. FUNCIONES PARA LEER TUS DATOS ---
@st.cache_data
def cargar_ocupados():
    df = pd.read_csv(LINK_OCUPADOS)
    df.columns = df.columns.str.upper().str.strip()
    return df

@st.cache_data
def cargar_reservas():
    # SOLUCIÓN: Leemos solo las columnas de la F a la J (índices 5 al 9) saltando la fila 1
    df = pd.read_csv(LINK_RESERVAS, skiprows=1, usecols=[5, 6, 7, 8, 9])
    
    # Las renombramos a la fuerza para que Python no se confunda con duplicados
    df.columns = ['FECHA', 'DÍA', 'BLOQUE', 'ESPACIO', 'MOTIVO']
    
    # Borramos filas que estén completamente vacías
    df_limpio = df.dropna(how='all') 
    return df_limpio

try:
    df_ocupados = cargar_ocupados()
    df_reservas = cargar_reservas()

    # --- 3. MENÚ DE BÚSQUEDA ---
    st.sidebar.header("🔍 Buscar horario:")
    dias = df_ocupados['DÍA'].dropna().unique()
    dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
    
    bloques = df_ocupados[df_ocupados['DÍA'] == dia_elegido]['BLOQUE'].dropna().unique()
    bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

    st.header(f"Resultados para: {dia_elegido} - Bloque {bloque_elegido}")

    # --- 4. RESERVAS ESPECIALES ---
    st.subheader("⚠️ Reservas Especiales")
    # Filtramos la tabla de reservas usando las columnas que renombramos
    reservas_filtradas = df_reservas[(df_reservas['DÍA'] == dia_elegido) & (df_reservas['BLOQUE'].astype(str) == str(bloque_elegido))]
    
    if not reservas_filtradas.empty:
        st.dataframe(reservas_filtradas, hide_index=True, use_container_width=True)
    else:
        st.success("No hay reservas especiales para este horario.")

    st.divider()

    # --- 5. ESPACIOS OCUPADOS ---
    st.subheader("🔴 Espacios Ocupados")
    ocupados_filtrado = df_ocupados[(df_ocupados['DÍA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
    
    if not ocupados_filtrado.empty:
        columnas_utiles = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
        columnas_existentes = [col for col in columnas_utiles if col in ocupados_filtrado.columns]
        st.dataframe(ocupados_filtrado[columnas_existentes], hide_index=True, use_container_width=True)
    else:
        st.write("No hay espacios ocupados registrados en este horario.")

except Exception as e:
    st.error(f"Error técnico: {e}")
