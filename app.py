import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")
# --- OCULTAR MENÚ SUPERIOR Y GITHUB ---
ocultar_menu = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
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
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    avisos_col_d = []
    
    col_avisos = -1
    for col in range(len(df_config.columns)):
        col_data = df_config.iloc[:, col].fillna("").astype(str)
        if col_data.str.contains("Espacios Bloqueados", case=False, na=False).any():
            col_avisos = col
            break
            
    if col_avisos != -1:
        avisos_brutos = df_config.iloc[:, col_avisos].fillna("").astype(str).tolist()
        for a in avisos_brutos:
            texto = a.strip()
            if texto and "ESPACIOS BLOQUEADOS" not in texto.upper() and texto.upper() != "NAN":
                if texto not in avisos_col_d:
                    avisos_col_d.append(texto)
    else:
        for col in range(len(df_config.columns)):
            for val in df_config.iloc[:, col].fillna("").astype(str):
                val_str = str(val).strip()
                if "⚠️" in val_str and val_str not in avisos_col_d:
                    avisos_col_d.append(val_str)

    def limpiar_bloque(val):
        val_str = str(val).strip().upper()
        if val_str.endswith('.0'):
            return val_str[:-2]
        return val_str

    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].apply(limpiar_bloque)
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()
        
    # --- Procesamos la columna SUBBLOQUE para que quede bonita ---
    if 'SUBBLOQUE' in df_o.columns:
        df_o['SUBBLOQUE'] = df_o['SUBBLOQUE'].astype(str).str.strip().str.upper()
        # Si la celda está vacía (NAN), la dejamos en blanco para que no moleste en la tabla
        df_o['SUBBLOQUE'] = df_o['SUBBLOQUE'].replace('NAN', '')

    espacios = df_o['ESPACIOS'].dropna().unique().tolist()
    espacios_totales = sorted([e for e in espacios if e != "NAN" and e != ""])
    
    return df_o, avisos_col_d, espacios_totales

try:
    df_ocupados, avisos_col_d, todos_los_espacios = cargar_datos()

    # --- MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        st.cache_data.clear()
        st.rerun()

    # --- PESTAÑAS PRINCIPALES ---
    tab1, tab2 = st.tabs(["🕰️ Buscar por Horario", "👤 Buscar Docente/Curso"])

    # --- PESTAÑA 1: HORARIO ---
    with tab1:
        col_dia, col_bloque = st.columns(2)
        
        dias = [d for d in df_ocupados['DIA'].dropna().unique() if d != "NAN"]
        with col_dia:
            dia_elegido = st.selectbox("📅 Día:", dias)
        
        # Cargamos los bloques normalmente
        bloques_raw = df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloques_limpios = [b for b in bloques_raw if b != "NAN"]
        bloques_ordenados = sorted(bloques_limpios, key=lambda x: int(x) if x.isdigit() else x)
        
        with col_bloque:
            bloque_elegido = st.selectbox("⏰ Bloque:", bloques_ordenados)

        st.divider()
        
        st.header(f"{dia_elegido} - Bloque {bloque_elegido}")

        # --- HORARIOS EXACTOS ---
        horarios = {
            "1": "7:40 a 9:00",
            "2": "9:10 a 10:30",
            "3": "10:45 a 12:05",
            "4": "12:15 a 13:35",
            "5": "13:45 a 15:05",
            "6": "15:10 a 16:30"
        }
        
        bloque_str = str(bloque_elegido).strip()
        if bloque_str in horarios:
            st.markdown(f"**⏱️ *{horarios[bloque_str]}***")

        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))]
        lista_ocupados = ocu['ESPACIOS'].dropna().tolist() if 'ESPACIOS' in ocu.columns else []
        espacios_libres = [espacio for espacio in todos_los_espacios if espacio not in lista_ocupados]

        # 1. MOSTRAR ESPACIOS LIBRES
        st.subheader("🟢 Ámbitos Libres")
        if espacios_libres:
            st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)))
        else:
            st.warning("No hay ningún ámbito libre en este horario.")

        # 2. MOSTRAR AVISOS
        st.subheader("📌 Reservas Especiales")
        if avisos_col_d:
            texto_avisos = "\n".join([f"- {aviso}" for aviso in avisos_col_d])
            st.warning(texto_avisos)
        else:
            st.info("No hay reservas especiales anotadas.")

        # 3. ACORDEÓN PARA CLASES REGULARES
        with st.expander("🔴 Ver Clases Regulares", expanded=False):
            if not ocu.empty:
                # AQUÍ SÍ DEJAMOS EL SUBBLOQUE
                cols_mostrar = ['BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
                cols_finales = [c for c in cols_mostrar if c in ocu.columns]
                st.dataframe(ocu[cols_finales], hide_index=True, use_container_width=True)
            else:
                st.info("No hay clases regulares registradas en este bloque.")

    # --- PESTAÑA 2: BÚSQUEDA ---
    with tab2:
        col_tipo, col_sel = st.columns(2)
        
        with col_tipo:
            tipo = st.radio("Buscar por:", ["Docente", "Curso"], horizontal=True)
        
        col_filtro = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col_filtro].dropna().unique() if str(x).upper() != "NAN"])
        
        with col_sel:
            sel = st.selectbox(f"Selecciona {tipo}:", lista)
        
        st.divider()
        
        st.header(f"Agenda de: {sel}")
        res_busqueda = df_ocupados[df_ocupados[col_filtro] == sel]
        
        # AQUÍ QUITAMOS EL SUBBLOQUE PARA NO CONFUNDIR
        cols_busqueda = ['DIA', 'BLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS', 'DOCENTES']
        cols_b_finales = [c for c in cols_busqueda if c in res_busqueda.columns]
        st.dataframe(res_busqueda[cols_b_finales], hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
