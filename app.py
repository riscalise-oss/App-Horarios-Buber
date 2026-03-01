import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")
st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=0&single=true&output=csv"

@st.cache_data
def cargar_datos():
    # 1. ASIGNACIONES (Clases regulares)
    df_o = pd.read_csv(LINK_OCUPADOS)
    # Limpiamos nombres de la hoja principal
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    # 2. RESERVAS ESPECIALES (El truco maestro)
    # Leemos la hoja "ciegos" (sin encabezados) para que no haya choque con los "Día" duplicados
    df_r_raw = pd.read_csv(LINK_RESERVAS, header=None)
    
    # Recortamos exactamente el bloque de Reservas (Columnas F a J -> índices 5 al 9)
    # Empezamos desde la fila 3 (índice 2) que es donde empiezan los datos reales
    df_r = df_r_raw.iloc[2:, 5:10].copy()
    
    # Les ponemos los nombres perfectos a la fuerza
    df_r.columns = ['FECHA', 'DIA', 'BLOQUE', 'ESPACIO', 'MOTIVO']
    df_r = df_r.dropna(how='all')
    
    # Extraemos todos los espacios posibles de las asignaciones
    espacios = df_o['ESPACIOS'].dropna().unique().tolist()
    
    return df_o, df_r, espacios

try:
    df_ocupados, df_reservas, todos_los_espacios = cargar_datos()

    # --- 3. MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    modo = st.sidebar.radio("Selecciona modo:", ["🕰️ Buscar por Horario", "🧑‍🏫 Buscar Docente/Curso"])
    st.sidebar.divider()

    # --- MODO 1: HORARIO ---
    if modo == "🕰️ Buscar por Horario":
        dias = df_ocupados['DIA'].dropna().unique()
        dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
        
        bloques = df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

        st.header(f"Resultados: {dia_elegido} - Bloque {bloque_elegido}")

        # Filtros precisos
        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'].astype(str) == str(bloque_elegido))]
        res = df_reservas[(df_reservas['DIA'] == dia_elegido) & (df_reservas['BLOQUE'].astype(str) == str(bloque_elegido))]

        # Lógica de Aulas Libres
        lista_ocupados = ocu['ESPACIOS'].dropna().astype(str).str.strip().tolist() if 'ESPACIOS' in ocu.columns else []
        lista_reservados = res['ESPACIO'].dropna().astype(str).str.strip().tolist() if 'ESPACIO' in res.columns else []
        espacios_en_uso = set(lista_ocupados + lista_reservados)
        espacios_libres = [espacio for espacio in todos_los_espacios if espacio not in espacios_en_uso]

        st.subheader("🟢 1. Espacios Totalmente Libres")
        if espacios_libres:
            st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)))
        else:
            st.warning("No hay ningún espacio libre en este horario.")

        st.subheader("⚠️ 2. Reservas Especiales")
        if not res.empty:
            st.dataframe(res, hide_index=True, use_container_width=True)
        else:
            st.info("No hay reservas especiales para este horario.")

        st.subheader("🔴 3. Clases Regulares")
        if not ocu.empty:
            cols_mostrar = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
            cols_finales = [c for c in cols_mostrar if c in ocu.columns]
            st.dataframe(ocu[cols_finales], hide_index=True, use_container_width=True)
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
