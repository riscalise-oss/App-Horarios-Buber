import streamlit as st
import pandas as pd
import base64
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")

# ==============================================================================
# --- FUNCIÓN PARA EL FONDO INSTITUCIONAL ---
# ==============================================================================
def aplicar_fondo_institucional(archivo_imagen):
    """
    Carga una imagen local, la convierte a base64 e inyecta el CSS 
    necesario para usarla como fondo de la aplicación.
    """
    if os.path.exists(archivo_imagen):
        try:
            with open(archivo_imagen, "rb") as f:
                data = f.read()
            img_base64 = base64.b64encode(data).decode()
            
            # CSS para el fondo
            page_bg_img = f'''
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{img_base64}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed; /* Mantiene el fondo quieto al hacer scroll */
            }}
            </style>
            '''
            st.markdown(page_bg_img, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error al cargar el fondo: {e}")
    else:
        st.warning(f"⚠️ No se encontró el archivo '{archivo_imagen}'. La app funcionará sin fondo personalizado.")
# ==============================================================================

# --- CSS LIMPIO Y SEGURO ---
ocultar_menu = """
    <style>
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    </style>
"""
st.markdown(ocultar_menu, unsafe_allow_html=True)

# 🚀 APLICAR EL FONDO INSTITUCIONAL 🚀
aplicar_fondo_institucional("fondo.png")

# --- DICCIONARIO TRADUCTOR DE BLOQUES ---
traductor_bloques = {
    "1": "1. 7:40 a 9:00",
    "2": "2. 9:10 a 10:30",
    "3": "3. 10:45 a 12:05",
    "4": "4. 12:15 a 13:35",
    "5": "5. 13:45 a 15:00",
    "6": "6. 15:10 a 16:30"
}

# --- TÍTULO CON LOGO ---
try:
    with open("logo.png", "rb") as f:
        data = f.read()
    img_base64 = base64.b64encode(data).decode()
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px; background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 10px;">
            <img src="data:image/png;base64,{img_base64}" width="70" style="margin-right: 15px; border-radius: 8px;">
            <h1 style="margin: 0; padding: 0; color: #31333F;">Buscador de Ámbitos</h1>
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
    
    # --- VACUNA: Eliminar columnas duplicadas ---
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    df_config = df_config.loc[:, ~df_config.columns.duplicated()].copy()
    
    # -- OPTIMIZACIÓN 1: Búsqueda Segura de Avisos (CORREGIDA) --
    avisos_col_d = []
    col_avisos = None
    col_desplaza = None
    
    # Buscamos las columnas de forma segura 1x1 para evitar el error de "Series is ambiguous"
    for col in df_config.columns:
        col_str = df_config[col].astype(str)
        if col_str.str.contains("Espacios Bloqueados", case=False, na=False).any():
            col_avisos = col
        if col_str.str.contains("Avisar al Profesor", case=False, na=False).any() or \
           col_str.str.contains("Desplaza a:", case=False, na=False).any():
            col_desplaza = col
            
    if col_avisos is not None:
        for idx, row in df_config.iterrows():
            aviso_ppal = str(row[col_avisos]).strip()
            
            # Filtramos celdas vacías o los títulos
            if aviso_ppal and aviso_ppal.upper() not in ["", "NAN", "ESPACIOS BLOQUEADOS / RESERVADOS", "ESPACIOS BLOQUEADOS"]:
                texto_final = aviso_ppal
                
                # Si encontramos la columna del profe, la pegamos
                if col_desplaza is not None:
                    aviso_profe = str(row[col_desplaza]).strip()
                    if aviso_profe and aviso_profe.upper() not in ["", "NAN", "AVISAR AL PROFESOR", "#N/A", "#REF!", "NONE"]:
                        texto_final = f"{aviso_ppal}   {aviso_profe}"
                        
                if texto_final not in avisos_col_d:
                    avisos_col_d.append(texto_final)
    else:
        # Plan de respaldo (Busca iconos de alerta directamente en toda la fila)
        for idx, row in df_config.iterrows():
            celdas_con_alerta = [str(x).strip() for x in row.values if pd.notna(x) and ("⚠️" in str(x) or "🔴" in str(x) or "🟡" in str(x))]
            if celdas_con_alerta:
                texto_unido = "   ".join(celdas_con_alerta)
                if texto_unido not in avisos_col_d:
                    avisos_col_d.append(texto_unido)

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
        
        # --- LÓGICA DE ESPACIOS LIBRES ---
        libres_completos = []
        libres_medio_1 = []
        libres_medio_2 = []
        libres_otros = []
        
        for e in todos_los_espacios:
            df_esp = ocu[ocu['ESPACIOS'] == e]
            
            if df_esp.empty:
                libres_completos.append(e)
            else:
                mask_almuerzo = df_esp.astype(str).apply(lambda row: row.str.contains('ALMUERZO', case=False)).any(axis=1)
                df_clases = df_esp[~mask_almuerzo]
                
                if df_clases.empty:
                    libres_completos.append(e)
                else:
                    ocupa_1 = False
                    ocupa_2 = False
                    ocupa_todo = False
                    
                    for sub in df_clases['SUBBLOQUE'].astype(str).str.strip().str.upper():
                        if sub == "NAN" or sub == "": ocupa_todo = True
                        elif sub.endswith("1"): ocupa_1 = True
                        elif sub.endswith("2"): ocupa_2 = True
                        else: ocupa_todo = True
                            
                    if ocupa_todo or (ocupa_1 and ocupa_2): pass 
                    elif ocupa_2 and not ocupa_1: libres_medio_1.append(e)
                    elif ocupa_1 and not ocupa_2: libres_medio_2.append(e)

        libres_completos = sorted(libres_completos)
        libres_medio_1 = sorted(libres_medio_1)
        libres_medio_2 = sorted(libres_medio_2)
        libres_otros = sorted(libres_otros)

        st.subheader("🟢 Ámbitos Libres")
        
        hay_libres = False
        
        if libres_completos:
            st.success("**Bloque Completo:**\n\n ✅ " + " | ✅ ".join(libres_completos))
            hay_libres = True
            
        if libres_medio_1:
            st.info("⏳ **1er Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(libres_medio
