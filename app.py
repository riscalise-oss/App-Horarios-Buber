import streamlit as st
import pandas as pd

# Configuración básica
st.set_page_config(page_title="Buscador de Espacios", layout="wide")

st.title("🏫 Buscador Rápido para Asistentes")
st.write("Encuentra al instante qué aulas están libres y quién está en cada espacio.")

# --- 1. TUS ENLACES SECRETOS ---
# ⚠️ REEMPLAZA ESTO CON TU ENLACE DE LA HOJA "ASIGNACIONES" (el primero que hicimos funcionar):
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhgZSlV_TATdDowWFQkR-R_hK-F-OGu5dYfwfErAjbPnWsQ4jrQvgfxpQFxs73dtKalvDV1_f-Ec21/pub?gid=727803976&single=true&output=csv"

# Este es el enlace de "Espacios libres" que me acabas de pasar:
LINK_LIBRES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5se3brxjtH9uEkXNlt03sha1MqpIwWYCbMH29Sz-Bsxz8R1PHcuPPJ-ERLQuEuC7wPP8fzIkOBVG/pub?gid=447717872&single=true&output=csv"

# --- 2. CARGAR LOS DATOS ---
@st.cache_data
def cargar_datos(link):
    df = pd.read_csv(link)
    df.columns = df.columns.str.upper().str.strip() # Limpia los nombres de las columnas
    return df

try:
    df_ocupados = cargar_datos(LINK_OCUPADOS)
    df_libres = cargar_datos(LINK_LIBRES)

    # --- 3. MENÚ DE BÚSQUEDA (A LA IZQUIERDA) ---
    st.sidebar.header("🔍 Buscar horario:")
    
    # Filtro de Día
    dias = df_ocupados['DÍA'].dropna().unique()
    dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
    
    # Filtro de Bloque
    bloques = df_ocupados[df_ocupados['DÍA'] == dia_elegido]['BLOQUE'].dropna().unique()
    bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

    st.header(f"Resultados para: {dia_elegido} - Bloque {bloque_elegido}")

    # --- 4. PRIORIDAD 1: ESPACIOS LIBRES ---
    st.subheader("🟢 1. Espacios Libres y Reservas")
    
    # Si la hoja de libres tiene las columnas DÍA y BLOQUE, la filtramos. Si no, mostramos todo.
    if 'DÍA' in df_libres.columns and 'BLOQUE' in df_libres.columns:
        libres_filtrado = df_libres[(df_libres['DÍA'] == dia_elegido) & (df_libres['BLOQUE'] == bloque_elegido)]
        st.dataframe(libres_filtrado, hide_index=True, use_container_width=True)
    else:
        st.dataframe(df_libres, hide_index=True, use_container_width=True)
        st.info("💡 Nota: Como no conozco las columnas de tu hoja de Libres, te muestro la lista completa. (Si me dices cómo se llaman las columnas de esa hoja, hago que se filtre sola por día y bloque también).")

    st.divider() # Línea separadora visual

    # --- 5. PRIORIDAD 2: ESPACIOS OCUPADOS ---
    st.subheader("🔴 2. Espacios Ocupados")
    ocupados_filtrado = df_ocupados[(df_ocupados['DÍA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
    
    if not ocupados_filtrado.empty:
        # Mostramos solo lo esencial para el asistente: Aula, Curso, Profesor y Materia
        columnas_utiles = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
        # Nos aseguramos de que existan para que no dé error
        columnas_existentes = [col for col in columnas_utiles if col in ocupados_filtrado.columns]
        
        st.dataframe(ocupados_filtrado[columnas_existentes], hide_index=True, use_container_width=True)
    else:
        st.write("No hay espacios ocupados registrados en este horario.")

except Exception as e:
    st.error(f"Hubo un error al leer los enlaces. Detalle técnico: {e}")
