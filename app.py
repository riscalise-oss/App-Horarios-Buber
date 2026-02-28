import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")

st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES (¡RELLENA LAS LÍNEAS 9 y 11!) ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5se3brxjtH9uEkXNlt03sha1MqpIwWYCbMH29Sz-Bsxz8R1PHcuPPJ-ERLQuEuC7wPP8fzIkOBVG/pub?gid=447717872&single=true&output=csv"
LINK_CONFIG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=0&single=true&output=csv"

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
    df = pd.read_csv(LINK_CONFIG, usecols=[6])
    df.columns = ['ESPACIOS_TOTALES']
    espacios = df['ESPACIOS_TOTALES'].dropna().astype(str).str.strip().unique().tolist()
    espacios = [e for e in espacios if e.upper() != "ESPACIOS" and e != ""]
    return espacios

try:
    df_ocupados = cargar_ocupados()
    df_reservas = cargar_reservas()
    todos_los_espacios = cargar_espacios_totales()

    # --- 3. SELECTOR DE MODO PRINCIPAL ---
    st.sidebar.header("⚙️ ¿Qué necesitas hacer?")
    modo = st.sidebar.radio("", ["🕰️ Buscar Espacios por Horario", "🧑‍🏫 Buscar Agenda de Docente/Curso"])
    
    st.sidebar.divider()

    # ==========================================
    # MODO 1: ESPACIOS POR HORARIO
    # ==========================================
    if modo == "🕰️ Buscar Espacios por Horario":
        st.sidebar.header("🔍 Elige el momento:")
        dias = df_ocupados['DÍA'].dropna().unique()
        dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
        
        bloques = df_ocupados[df_ocupados['DÍA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

        st.header(f"Resultados para: {dia_elegido} - Bloque {bloque_elegido}")

        ocupados_filtrado = df_ocupados[(df_ocupados['DÍA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
        reservas_filtradas = df_reservas[(df_reservas['DÍA'] == dia_elegido) & (df_reservas['BLOQUE'].astype(str) == str(bloque_elegido))]

        lista_ocupados = ocupados_filtrado['ESPACIOS'].dropna().astype(str).str.strip().tolist() if 'ESPACIOS' in ocupados_filtrado.columns else []
        lista_reservados = reservas_filtradas['ESPACIO'].dropna().astype(str).str.strip().tolist() if 'ESPACIO' in reservas_filtradas.columns else []
        espacios_en_uso = set(lista_ocupados + lista_reservados)

        espacios_libres = [espacio for espacio in todos_los_espacios if espacio not in espacios_en_uso]

        st.subheader("🟢 1. Espacios Totalmente Libres")
        if espacios_libres:
            st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)))
        else:
            st.warning("No hay ningún espacio libre en este horario.")

        st.divider()

        st.subheader("⚠️ 2. Reservas Especiales (Imprevistos)")
        if not reservas_filtradas.empty:
            st.dataframe(reservas_filtradas, hide_index=True, use_container_width=True)
        else:
            st.info("No hay reservas especiales para este horario.")

        st.divider()

        st.subheader("🔴 3. Clases Regulares (Ocupados)")
        if not ocupados_filtrado.empty:
            columnas_utiles = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
            columnas_existentes = [col for col in columnas_utiles if col in ocupados_filtrado.columns]
            st.dataframe(ocupados_filtrado[columnas_existentes], hide_index=True, use_container_width=True)
        else:
            st.write("No hay clases regulares registradas en este horario.")

    # ==========================================
    # MODO 2: AGENDA DE DOCENTE O CURSO
    # ==========================================
    else:
        st.sidebar.header("🔎 Buscar Agenda")
        
        lista_docentes = sorted([d for d in df_ocupados['DOCENTES'].dropna().unique() if str(d).strip() != ""])
        lista_cursos = sorted([c for c in df_ocupados['CURSOS'].dropna().unique() if str(c).strip() != ""])
        
        opciones_docentes = ["-- Seleccionar --"] + lista_docentes
        opciones_cursos = ["-- Seleccionar --"] + lista_cursos
        
        # Un sub-botón para elegir si buscamos docente o curso
        tipo_filtro = st.sidebar.radio("Buscar por:", ["Docente", "Curso"])

        if tipo_filtro == "Docente":
            seleccion = st.sidebar.selectbox("👩‍🏫 Elige Docente:", opciones_docentes)
            columna_filtro = 'DOCENTES'
        else:
            seleccion = st.sidebar.selectbox("🎓 Elige Curso:", opciones_cursos)
            columna_filtro = 'CURSOS'

        if seleccion != "-- Seleccionar --":
            st.header(f"Agenda de: {seleccion}")
            st.write("Mostrando todos los horarios registrados en la semana para esta búsqueda.")
            
            filtro = df_ocupados[df_ocupados[columna_filtro] == seleccion]
            
            if not filtro.empty:
                columnas = ['DÍA', 'BLOQUE', 'ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
                cols_ok = [c for c in columnas if c in filtro.columns]
                st.dataframe(filtro[cols_ok], hide_index=True, use_container_width=True)
            else:
                st.warning("No hay horarios registrados para esta selección.")
        else:
            st.info("👈 Por favor, selecciona un nombre o curso en el menú de la izquierda para ver su agenda completa.")

except Exception as e:
    st.error(f"Error técnico: {e}")
