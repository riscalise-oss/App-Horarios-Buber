import streamlit as st
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")

# --- CSS LIMPIO Y SEGURO ---
ocultar_menu = """
    <style>
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    </style>
"""
st.markdown(ocultar_menu, unsafe_allow_html=True)

# --- DICCIONARIO TRADUCTOR DE BLOQUES ---
traductor_bloques = {
    "1": "1. 7:40 a 9:00",
    "2": "2. 9:10 a 10:30",
    "3": "3. 10:45 a 12:05",
    "4": "4. 12:15 a 12:55 ; 12:55 a 13:35",
    "5": "5. 13:45 a 15:00",
    "6": "6. 15:10 a 16:30"
}

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
    
    # -- OPTIMIZACIÓN 1: Búsqueda Vectorizada de Avisos --
    avisos_col_d = []
    mask_bloqueados = df_config.apply(lambda col: col.astype(str).str.contains("Espacios Bloqueados", case=False, na=False))
    cols_con_bloqueados = mask_bloqueados.any()
    
    if cols_con_bloqueados.any():
        col_avisos = cols_con_bloqueados.idxmax()
        col_data = df_config[col_avisos].fillna("").astype(str).str.strip()
        filtro_validos = (col_data != "") & (~col_data.str.upper().str.contains("ESPACIOS BLOQUEADOS")) & (col_data.str.upper() != "NAN")
        avisos_col_d = col_data[filtro_validos].unique().tolist()
    else:
        valores_planos = df_config.fillna("").astype(str).values.flatten()
        celdas_alerta = pd.Series(valores_planos)[pd.Series(valores_planos).str.contains("⚠️")]
        avisos_col_d = celdas_alerta.str.strip().unique().tolist()

    # -- OPTIMIZACIÓN 2: Limpieza de Columnas Vectorizada --
    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "MIÉRCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df_o['ORDEN_DIA'] = df_o['DIA'].map(orden_dias)

    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        df_o['ORDEN_BLOQUE'] = pd.to_numeric(df_o['BLOQUE'], errors='coerce').fillna(99)
        
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()
        
    if 'SUBBLOQUE' in df_o.columns:
        df_o['SUBBLOQUE'] = df_o['SUBBLOQUE'].astype(str).str.strip().str.upper().replace('NAN', '')

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
        
        bloque_elegido = col_bloque.selectbox(
            "⏰ Bloque:", 
            bloques_ordenados,
            format_func=lambda x: traductor_bloques.get(str(x), f"Bloque {x}")
        )

        st.divider()
        
        bloque_texto = traductor_bloques.get(str(bloque_elegido), f"Bloque {bloque_elegido}")
        st.header(f"{dia_elegido} - {bloque_texto}")

        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))].copy()
        
        # --- NUEVA LÓGICA DE ESPACIOS LIBRES (REPLICA SHEETS) ---
        libres_completos = []
        libres_parciales = []
        
        for e in todos_los_espacios:
            df_esp = ocu[ocu['ESPACIOS'] == e]
            
            if df_esp.empty:
                # El aula está 100% vacía
                libres_completos.append(e)
            else:
                # Buscar "ALMUERZO" en toda la fila para ser a prueba de balas
                mask_almuerzo = df_esp.astype(str).apply(lambda row: row.str.contains('ALMUERZO', case=False)).any(axis=1)
                almuerzos = mask_almuerzo.sum()
                totales = len(df_esp)
                normales = totales - almuerzos
                
                if normales == 0:
                    # Si solo hay almuerzos, mostramos el aula limpia
                    libres_completos.append(e)
                elif normales > 0 and almuerzos > 0:
                    # Hay clase + almuerzo. Extraemos el subbloque
                    fila_almuerzo = df_esp[mask_almuerzo].iloc[0]
                    sub_alm = str(fila_almuerzo.get('SUBBLOQUE', '')).strip()
                    
                    if sub_alm and sub_alm.upper() != "NAN":
                        libres_parciales.append(f"{e} ({sub_alm})")
                    else:
                        libres_parciales.append(f"{e} (Almuerzo)")

        # Ordenamos ambas listas alfabéticamente por separado
        libres_completos = sorted(libres_completos)
        libres_parciales = sorted(libres_parciales)

        # Construimos el texto final a mostrar
        texto_mostrar = ""
        
        if libres_completos:
            texto_mostrar += " ✅ " + " | ✅ ".join(libres_completos)
            
        if libres_parciales:
            if texto_mostrar:
                # Si ya hay espacios completos, agregamos un separador antes de los parciales
                texto_mostrar += "   |   " 
            # Usamos un check más oscuro para los parciales
            texto_mostrar += " ✔️ " + " | ✔️ ".join(libres_parciales)

        st.subheader("🟢 Ámbitos Libres")
        if texto_mostrar:
            st.success(texto_mostrar)
        else:
            st.success("No hay espacios libres.")

        st.subheader("📌 Reservas Especiales")
        if avisos_col_d: st.warning("\n".join([f"- {a}" for a in avisos_col_d]))
        else: st.info("No hay reservas.")

        with st.expander("🔴 Ver Clases Regulares", expanded=False):
            if not ocu.empty:
                if 'BLOQUE' in ocu.columns:
                    ocu['BLOQUE'] = ocu['BLOQUE'].astype(str).replace(traductor_bloques)
                    
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
        
        res = df_ocupados[df_ocupados[col_filtro] == sel].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE']).copy()
        
        if 'BLOQUE' in res.columns:
            res['BLOQUE'] = res['BLOQUE'].astype(str).replace(traductor_bloques)
            
        cols = [c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res.columns]
        st.dataframe(res[cols], hide_index=True, use_container_width=True)

    # --- PESTAÑA 3: BUSCAR POR ÁMBITO ---
    with tab3:
        espacio_sel = st.selectbox("📍 Selecciona el Ámbito:", todos_los_espacios)
        st.divider()
        st.header(f"Agenda de: {espacio_sel}")
        
        res_e = df_ocupados[df_ocupados['ESPACIOS'] == espacio_sel].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE']).copy()
        
        if 'BLOQUE' in res_e.columns:
            res_e['BLOQUE'] = res_e['BLOQUE'].astype(str).replace(traductor_bloques)
            
        cols = [c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res_e.columns]
        st.dataframe(res_e[cols], hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")

# --- PIE DE PÁGINA PERSONALIZADO ---
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
