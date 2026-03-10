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
    
    # --- VACUNA: Eliminar columnas duplicadas para evitar errores ---
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    # --- VACUNA: Eliminar columnas duplicadas también aquí ---
    df_config = df_config.loc[:, ~df_config.columns.duplicated()].copy()
    
    # -- OPTIMIZACIÓN 1: Búsqueda Vectorizada de Avisos (AHORA UNIFICANDO AL PROFESOR) --
    avisos_col_d = []
    
    # Buscamos dinámicamente en qué columna está el aviso y en cuál el profesor
    mask_bloqueados = df_config.apply(lambda col: col.astype(str).str.contains("Espacios Bloqueados", case=False, na=False))
    mask_desplaza = df_config.apply(lambda col: col.astype(str).str.contains("Avisar al Profesor", case=False, na=False) | col.astype(str).str.contains("Desplaza a:", case=False, na=False))
    
    col_avisos = mask_bloqueados.idxmax() if mask_bloqueados.any() else None
    col_desplaza = mask_desplaza.idxmax() if mask_desplaza.any() else None
    
    if col_avisos is not None:
        for idx, row in df_config.iterrows():
            aviso_ppal = str(row[col_avisos]).strip()
            
            # Filtramos celdas vacías o los títulos
            if aviso_ppal and aviso_ppal.upper() not in ["", "NAN", "ESPACIOS BLOQUEADOS"]:
                texto_final = aviso_ppal
                
                # Si encontramos la columna del profe y tiene datos, la pegamos al lado
                if col_desplaza is not None:
                    aviso_profe = str(row[col_desplaza]).strip()
                    # Ignoramos celdas con errores típicos de Sheets o vacías
                    if aviso_profe and aviso_profe.upper() not in ["", "NAN", "AVISAR AL PROFESOR", "#N/A", "#REF!", "NONE"]:
                        texto_final = f"{aviso_ppal}   {aviso_profe}"
                        
                if texto_final not in avisos_col_d:
                    avisos_col_d.append(texto_final)
    else:
        # Plan de respaldo (idéntico a tu lógica original pero agrupando fila por fila)
        for idx, row in df_config.iterrows():
            # Extraemos cualquier celda de la fila que tenga el ícono ⚠️
            celdas_con_alerta = [str(x).strip() for x in row.values if pd.notna(x) and "⚠️" in str(x)]
            if celdas_con_alerta:
                # Si en una misma fila encuentra la reserva y al profe desplazado, los une
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
        
        # --- NUEVA LÓGICA DE ESPACIOS LIBRES (ESTRICTA Y SEGURA) ---
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
            st.info("⏳ **1er Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(libres_medio_1))
            hay_libres = True
            
        if libres_medio_2:
            st.info("⏳ **2do Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(libres_medio_2))
            hay_libres = True
            
        if libres_otros:
            st.info("⏳ **Otros libres parciales:**\n\n ✔️ " + " | ✔️ ".join(libres_otros))
            hay_libres = True

        if not hay_libres:
            st.error("No hay espacios libres en este bloque.")

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
