import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")

st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES ---
# ⚠️ 1. Tu enlace original de Asignaciones:
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhgZSlV_TATdDowWFQkR-R_hK-F-OGu5dYfwfErAjbPnWsQ4jrQvgfxpQFxs73dtKalvDV1_f-Ec21/pub?gid=727803976&single=true&output=csv"

# ⚠️ 2. Tu enlace de Reservas Especiales:
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5se3brxjtH9uEkXNlt03sha1MqpIwWYCbMH29Sz-Bsxz8R1PHcuPPJ-ERLQuEuC7wPP8fzIkOBVG/pub?gid=447717872&single=true&output=csv"

# ⚠️ 3. PEGA AQUÍ TU NUEVO ENLACE DE LA HOJA "CONFIGURACIÓN":
LINK_CONFIG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5se3brxjtH9uEkXNlt03sha1MqpIwWYCbMH29Sz-Bsxz8R1PHcuPPJ-ERLQuEuC7wPP8fzIkOBVG/pub?gid=0&single=true&output=csv"

# --- 2. FUNCIONES PARA LEER TUS DATOS ---
@st.cache_data
def cargar_ocupados():
    df = pd.read_csv(LINK_OCUPADOS)
    df.columns = df.columns.str.upper().str.strip()
    return df

@st.cache_data
def cargar_reservas():
    df = pd.read_csv(LINK_RESERVAS, skiprows=1, usecols=[5, 6, 7, 8, 9])
    df.columns = ['FECHA', 'DÍA', 'BLOQUE', 'ESPACIO', 'MOTIVO']
    return df.dropna(how='all')

@st.cache_data
def cargar_espacios_totales():
    # Leemos solo la columna G (índice 6) de la hoja Configuración
    df = pd.read_csv(LINK_CONFIG, usecols=[6])
    df.columns = ['ESPACIOS_TOTALES']
    # Limpiamos vacíos y nos quedamos con una lista única
    espacios = df['ESPACIOS_TOTALES'].dropna().astype(str).str.strip().unique().tolist()
    # Quitamos la palabra del encabezado si se coló en la lista
    espacios = [e for e in espacios if e.upper() != "ESPACIOS" and e != ""]
    return espacios

try:
    df_ocupados = cargar_ocupados()
    df_reservas = cargar_reservas()
    todos_los_espacios = cargar_espacios_totales()

    # --- 3. MENÚ DE BÚSQUEDA ---
    st.sidebar.header("🔍 Buscar horario:")
    dias = df_ocupados['DÍA'].dropna().unique()
    dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
    
    bloques = df_ocupados[df_ocupados['DÍA'] == dia_elegido]['BLOQUE'].dropna().unique()
    bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

    st.header(f"Resultados para: {dia_elegido} - Bloque {bloque_elegido}")

    # Filtramos Ocupados y Reservas para el día y bloque elegido
    ocupados_filtrado = df_ocupados[(df_ocupados['DÍA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
    reservas_filtradas = df_reservas[(df_reservas['DÍA'] == dia_elegido) & (df_reservas['BLOQUE'].astype(str) == str(bloque_elegido))]

    # Hacemos la lista de los que están en uso
    lista_ocupados = ocupados_filtrado['ESPACIOS'].dropna().astype(str).str.strip().tolist() if 'ESPACIOS' in ocupados_filtrado.columns else []
    lista_reservados = reservas_filtradas['ESPACIO'].dropna().astype(str).str.strip().tolist() if 'ESPACIO' in reservas_filtradas.columns else []
    espacios_en_uso = set(lista_ocupados + lista_reservados)

    # LA MAGIA: Calculamos los libres
    espacios_libres = [espacio for espacio in todos_los_espacios if espacio not in espacios_en_uso]

    # --- 4. PRIORIDAD 1: ESPACIOS LIBRES ---
    st.subheader("🟢 1. Espacios Totalmente Libres")
    if espacios_libres:
        # Los mostramos en un formato bonito
        st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)))
    else:
        st.warning("No hay ningún espacio libre en este horario.")

    st.divider()

    # --- 5. RESERVAS ESPECIALES ---
    st.subheader("⚠️ 2. Reservas Especiales (Imprevistos)")
    if not reservas_filtradas.empty:
        st.dataframe(reservas_filtradas, hide_index=True, use_container_width=True)
    else:
        st.info("No hay reservas especiales para este horario.")

    st.divider()

    # --- 6. ESPACIOS OCUPADOS ---
    st.subheader("🔴 3. Clases Regulares (Ocupados)")
    if not ocupados_filtrado.empty:
        columnas_utiles = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
        columnas_existentes = [col for col in columnas_utiles if col in ocupados_filtrado.columns]
        st.dataframe(ocupados_filtrado[columnas_existentes], hide_index=True, use_container_width=True)
    else:
        st.write("No hay clases regulares registradas en este horario.")

except Exception as e:
    st.error(f"Error técnico: {e}")
