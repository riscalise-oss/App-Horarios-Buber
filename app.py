import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")

# --- CSS MÍNIMO Y EFICIENTE ---
st.markdown("""
    <style>
    /* Ocultamos el header nativo de forma directa */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Ocultamos el menú principal (hamburguesa) */
    #MainMenu {
        visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)
# --- TÍTULO CON LOGO ---
try:
    with open("logo.png", "rb") as f:
        data = f.read()
    img_base64 = base64.b64encode(data).decode()
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{img_base64}" width="70" style="margin-right: 15px; border-radius: 8px;">
            <h1 style="margin: 0; padding: 0;">Buscador de Ámbitos</h1>
        </div>
    """, unsafe_allow_html=True)
except Exception:
    st.title("🛡️ Buscador de Ámbitos")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    # Carga de datos
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    # -- OPTIMIZACIÓN 1: Búsqueda Vectorizada de Avisos --
    avisos_col_d = []
    
    # Buscar "Espacios Bloqueados" en todo el DataFrame a la vez
    mask_bloqueados = df_config.apply(lambda col: col.astype(str).str.contains("Espacios Bloqueados", case=False, na=False))
    cols_con_bloqueados = mask_bloqueados.any()
    
    if cols_con_bloqueados.any():
        col_avisos = cols_con_bloqueados.idxmax() # Toma la primera columna donde aparezca
        col_data = df_config[col_avisos].fillna("").astype(str).str.strip()
        # Filtramos valores válidos directamente
        filtro_validos = (col_data != "") & (~col_data.str.upper().str.contains("ESPACIOS BLOQUEADOS")) & (col_data.str.upper() != "NAN")
        avisos_col_d = col_data[filtro_validos].unique().tolist()
    else:
        # Si no lo encuentra, buscamos "⚠️" aplastando el DataFrame en una sola lista (muy rápido)
        valores_planos = df_config.fillna("").astype(str).values.flatten()
        celdas_alerta = pd.Series(valores_planos)[pd.Series(valores_planos).str.contains("⚠️")]
        avisos_col_d = celdas_alerta.str.strip().unique().tolist()

    # -- OPTIMIZACIÓN 2: Limpieza de Columnas Vectorizada --
    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIÉRCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df_o['ORDEN_DIA'] = df_o['DIA'].map(orden_dias)

    if 'BLOQUE' in df_o.columns:
        # Limpia el '.0' final usando regex, sin usar la función lenta .apply()
        df_o['BLOQUE'] = df_o['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()
        
    if 'SUBBLOQUE' in df_o.columns:
        df_o['SUBBLOQUE'] = df_o['SUBBLOQUE'].astype(str).str.strip().str.upper().replace('NAN', '')

    # Extraer espacios únicos
    if 'ESPACIOS' in df_o.columns:
        espacios_sucios = df_o['ESPACIOS'].dropna().unique()
        espacios = sorted([e for e in espacios_sucios if e not in ["NAN", ""]])
    else:
        espacios = []
    
    return df_o, avisos_col_d, espacios

try:
    df_ocupados, avisos_col_d, todos_los_espacios = cargar_datos()

    st.sidebar.header("⚙️ Opciones")
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["🕰️ Buscar por Horario", "👤 Buscar Docente/Curso", "📍 Buscar por Ámbito"])

    # --- PESTAÑA 1: HORARIO ---
    with tab1:
        col_dia, col_bloque = st.columns(2)
        dias_disponibles = df_ocupados.sort_values('ORDEN_DIA')['DIA'].dropna().unique().tolist()
        dia_elegido = col_dia.selectbox("📅 Día:", dias_disponibles)
        
        bloques_raw = df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloques_ordenados = sorted([b for b in bloques_raw if b != "NAN"], key=lambda x: int(x) if x.isdigit() else x)
        bloque_elegido = col_bloque.selectbox("⏰ Bloque:", bloques_ordenados)

        st.divider()
        st.header(f"{dia_elegido} - Bloque {bloque_elegido}")

        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))]
        lista_ocupados = ocu['ESPACIOS'].dropna().tolist() if 'ESPACIOS' in ocu.columns else []
        espacios_libres = [e for e in todos_los_espacios if e not in lista_ocupados]

        st.subheader("🟢 Ámbitos Libres")
        st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)) if espacios_libres else "No hay espacios libres.")

        st.subheader("📌 Reservas Especiales")
        if avisos_col_d: st.warning("\n".join([f"- {a}" for a in avisos_col_d]))
        else: st.info("No hay reservas.")

        with st.expander("🔴 Ver Clases Regulares", expanded=False):
            if not ocu.empty:
                cols = [c for c in ['BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA'] if c in ocu.columns]
                st.dataframe(ocu[cols], hide_index=True, use_container_width=True)

    # --- PESTAÑA 2: BUSCAR DOCENTE/CURSO ---
    with tab2:
        tipo = st.radio("Buscar por:", ["Docente", "Curso"], horizontal=True)
        col_filtro = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col_filtro].dropna().unique() if str(x).upper() != "NAN"])
        sel = st.selectbox(f"Selecciona {tipo}:", lista)
        st.divider()
        st.header(f"Agenda de: {sel}")
        res = df_ocupados[df_ocupados[col_filtro] == sel].sort_values(['ORDEN_DIA', 'BLOQUE'])
        cols = [c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res.columns]
        st.dataframe(res[cols], hide_index=True, use_container_width=True)

    # --- PESTAÑA 3: BUSCAR POR ÁMBITO ---
    with tab3:
        espacio_sel = st.selectbox("📍 Selecciona el Ámbito:", todos_los_espacios)
        st.divider()
        st.header(f"Agenda de: {espacio_sel}")
        res_e = df_ocupados[df_ocupados['ESPACIOS'] == espacio_sel].sort_values(['ORDEN_DIA', 'BLOQUE'])
        cols = [c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res_e.columns]
        st.dataframe(res_e[cols], hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")

# --- PIE DE PÁGINA PERSONALIZADO ("by Richard") ---
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        font-size: 12px;
        color: grey;
        padding: 10px;
        background-color: transparent;
        z-index: 100;
    }
    </style>
    <div class="footer">
        by Richard
    </div>
""", unsafe_allow_html=True)
