import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")
st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=0&single=true&output=csv"

@st.cache_data
def cargar_datos():
    # 1. LEER ARCHIVOS
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    df_r_raw = pd.read_csv(LINK_RESERVAS, header=None)
    df_r = df_r_raw.iloc[2:, 5:10].copy()
    df_r.columns = ['FECHA', 'DIA', 'BLOQUE', 'ESPACIO', 'MOTIVO']
    df_r = df_r.dropna(how='all')

    # 2. LIMPIEZA PROFUNDA DE DATOS (El arreglo para que no muestre aulas libres por error)
    # Convertimos todo el contenido a texto, mayúsculas y borramos espacios invisibles
    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].astype(str).str.strip().str.upper()
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()

    if 'DIA' in df_r.columns:
        df_r['DIA'] = df_r['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
    if 'BLOQUE' in df_r.columns:
        df_r['BLOQUE'] = df_r['BLOQUE'].astype(str).str.strip().str.upper()
    if 'ESPACIO' in df_r.columns:
        df_r['ESPACIO'] = df_r['ESPACIO'].astype(str).str.strip().str.upper()

    # 3. LISTA DE ESPACIOS TOTALES
    # Sacamos la lista maestra limpiando los valores nulos
    espacios = df_o['ESPACIOS'].dropna().unique().tolist()
    espacios_totales = sorted([e for e in espacios if e != "NAN" and e != ""])
    
    return df_o, df_r, espacios_totales

try:
    df_ocupados, df_reservas, todos_los_espacios = cargar_datos()

    # --- 3. MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    modo = st.sidebar.radio("Selecciona modo:", ["🕰️ Buscar por Horario", "🧑‍🏫 Buscar Docente/Curso"])
    st.sidebar.divider()

    # --- MODO 1: HORARIO ---
    if modo == "🕰️ Buscar por Horario":
        dias = [d for d in df_ocupados['DIA'].dropna().unique() if d != "NAN"]
        dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
        
        bloques = [b for b in df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique() if b != "NAN"]
        bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

        st.header(f"Resultados: {dia_elegido} - Bloque {bloque_elegido}")

        # Filtros exactos
        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
        res = df_reservas[(df_reservas['DIA'] == dia_elegido) & (df_reservas['BLOQUE'] == bloque_elegido)]

        # Lógica de Aulas Libres y Ocupadas
        lista_ocupados = ocu['ESPACIOS'].dropna().tolist() if 'ESPACIOS' in ocu.columns else []
        lista_reservados = res['ESPACIO'].dropna().tolist() if 'ESPACIO' in res.columns else []
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
            st.write("No hay clases regulares registradas.")

    # --- MODO 2: BÚSQUEDA ---
    else:
        tipo = st.sidebar.radio("Buscar por:", ["Docente", "Curso"])
        col = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col].dropna().unique() if str(x).upper() != "NAN"])
        sel = st.sidebar.selectbox(f"Selecciona {tipo}:", lista)
        
        st.header(f"Agenda de: {sel}")
        res_busqueda = df_ocupados[df_ocupados[col] == sel]
        st.dataframe(res_busqueda, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
