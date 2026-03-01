import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")

st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES (¡RELLENA AQUÍ!) ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=0&single=true&output=csv"

# --- 2. FUNCIONES DE CARGA ---
@st.cache_data
def cargar_ocupados():
    df = pd.read_csv(LINK_OCUPADOS)
    df.columns = [str(c).upper().strip() for c in df.columns]
    return df

@st.cache_data
def cargar_reservas():
    # Leemos el csv y tomamos la fila 1 como encabezados
    df = pd.read_csv(LINK_RESERVAS, header=1)
    # Limpiamos nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]
    # Filtramos solo lo necesario
    cols_necesarias = ['DÍA', 'BLOQUE', 'ESPACIO', 'MOTIVO']
    # Nos aseguramos que las columnas existan
    df = df[[c for c in cols_necesarias if c in df.columns]]
    return df.dropna(how='all')

@st.cache_data
def cargar_espacios():
    df = pd.read_csv(LINK_RESERVAS, header=1)
    espacios = df.iloc[:, 3].dropna().unique() # Asumiendo columna ESPACIO en la tabla de reservas
    return [e for e in espacios if str(e).strip() != ""]

try:
    df_ocupados = cargar_ocupados()
    df_reservas = cargar_reservas()

    # --- 3. MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    modo = st.sidebar.radio("Selecciona modo:", ["🕰️ Buscar por Horario", "🧑‍🏫 Buscar Docente/Curso"])
    st.sidebar.divider()

    # --- MODO 1: HORARIO ---
    if modo == "🕰️ Buscar por Horario":
        dias = df_ocupados['DÍA'].dropna().unique()
        dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
        bloques = df_ocupados[df_ocupados['DÍA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

        st.header(f"Resultados: {dia_elegido} - Bloque {bloque_elegido}")

        # Filtros
        ocu = df_ocupados[(df_ocupados['DÍA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
        res = df_reservas[(df_reservas['DÍA'] == dia_elegido) & (df_reservas['BLOQUE'].astype(str) == str(bloque_elegido))]

        # 1. Reservas Especiales
        st.subheader("⚠️ Reservas Especiales")
        if not res.empty:
            st.dataframe(res, hide_index=True, use_container_width=True)
        else:
            st.info("No hay reservas especiales.")

        # 2. Clases Regulares
        st.subheader("🔴 Clases Regulares")
        if not ocu.empty:
            st.dataframe(ocu[['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']], hide_index=True, use_container_width=True)
        else:
            st.write("No hay clases regulares.")

    # --- MODO 2: BÚSQUEDA ---
    else:
        tipo = st.sidebar.radio("Buscar por:", ["Docente", "Curso"])
        col = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted(df_ocupados[col].dropna().unique())
        sel = st.sidebar.selectbox(f"Selecciona {tipo}:", lista)
        
        st.header(f"Agenda de: {sel}")
        res_busqueda = df_ocupados[df_ocupados[col] == sel]
        st.dataframe(res_busqueda, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
