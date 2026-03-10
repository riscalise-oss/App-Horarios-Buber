import streamlit as st
import pandas as pd
import base64
import datetime

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

# --- ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')

    # -- Limpieza de Columnas Vectorizada --
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
    
    return df_o, df_config, espacios

try:
    df_ocupados, df_config, todos_los_espacios = cargar_datos()

    tab1, tab2, tab3 = st.tabs(["🕰️ Buscar por Horario", "👤 Buscar Docente/Curso", "📍 Buscar por Ámbito"])

    # --- PESTAÑA 1: HORARIO ---
    with tab1:
        col_fecha, col_dia, col_bloque = st.columns([1.5, 1.5, 1])
        
        fecha_elegida = col_fecha.date_input("📅 Fecha de reserva:", datetime.date.today())
        
        dias_semana = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
        dia_auto = dias_semana[fecha_elegida.weekday()]
        
        dias_disponibles = df_ocupados.sort_values('ORDEN_DIA')['DIA'].dropna().unique().tolist()
        index_dia = dias_disponibles.index(dia_auto) if dia_auto in dias_disponibles else 0
        
        dia_elegido = col_dia.selectbox("📅 Día (Automático):", dias_disponibles, index=index_dia)
        
        bloques_raw = df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloques_ordenados = sorted([b for b in bloques_raw if b != "NAN"], key=lambda x: int(x) if x.isdigit() else x)
        
        bloque_elegido = col_bloque.selectbox(
            "⏰ Bloque:", 
            bloques_ordenados,
            format_func=lambda x: traductor_bloques.get(str(x), f"Bloque {x}")
        )

        st.divider()
        
        bloque_texto = traductor_bloques.get(str(bloque_elegido), f"Bloque {bloque_elegido}")
        st.header(f"{fecha_elegida.strftime('%d/%m/%Y')} | {dia_elegido} - {bloque_texto}")

        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))].copy()
        
        # --- LÓGICA DE INTERCEPCIÓN DE RESERVAS ESPECIALES (MEJORADA) ---
        espacios_reservados_hoy = []
        alertas_desplazamiento = []
        
        # Todas las formas posibles en las que Google Sheets o Pandas podrían exportar la fecha
        f1 = fecha_elegida.strftime("%d/%m/%Y") # 09/03/2026
        f2 = f"{fecha_elegida.day}/{fecha_elegida.month}/{fecha_elegida.year}" # 9/3/2026
        f3 = fecha_elegida.strftime("%Y-%m-%d") # 2026-03-09
        f4 = f"{fecha_elegida.day}/{fecha_elegida.strftime('%m')}/{fecha_elegida.year}" # 9/03/2026 (TU FORMATO EXACTO)
        f5 = f"{fecha_elegida.strftime('%d')}/{fecha_elegida.month}/{fecha_elegida.year}" # 09/3/2026
        
        posibles_fechas = [f1, f2, f3, f4, f5]
        
        for idx, row in df_config.astype(str).iterrows():
            fila_lista = [str(x).strip().upper() for x in row.values if str(x).upper() != "NAN"]
            
            # Chequeo flexible de fecha y bloque
            match_fecha = any(f in c for c in fila_lista for f in posibles_fechas)
            match_bloque = any(str(bloque_elegido) == c or f"{bloque_elegido}.0" == c for c in fila_lista)
            
            if match_fecha and match_bloque:
                for e in todos_los_espacios:
                    # Buscamos si el nombre del aula está en alguna celda de esta fila
                    if any(e in c for c in fila_lista):
                        espacios_reservados_hoy.append(e)
        
        espacios_reservados_hoy = list(set(espacios_reservados_hoy))
        
        # Identificar al profesor desplazado
        for e in espacios_reservados_hoy:
            df_esp_fijo = ocu[ocu['ESPACIOS'] == e]
            if not df_esp_fijo.empty:
                df_clases = df_esp_fijo[~df_esp_fijo.astype(str).apply(lambda r: r.str.contains('ALMUERZO', case=False)).any(axis=1)]
                if not df_clases.empty:
                    profs = [p for p in df_clases['DOCENTES'].unique() if str(p).upper() not in ["NAN", ""]]
                    mats = [m for m in df_clases['MATERIA'].unique() if str(m).upper() not in ["NAN", ""]]
                    str_profs = " y ".join(profs) if profs else "Docente no asignado"
                    str_mats = " - ".join(mats) if mats else "Materia no asignada"
                    alertas_desplazamiento.append(f"⚠️ **{e}** reservado. Desplaza a: **{str_profs}** ({str_mats})")
                else:
                    alertas_desplazamiento.append(f"✅ **{e}** reservado. (Estaba libre en horario fijo)")
            else:
                alertas_desplazamiento.append(f"✅ **{e}** reservado. (Estaba libre en horario fijo)")

        # --- LÓGICA DE ESPACIOS LIBRES ---
        libres_completos = []
        libres_medio_1 = []
        libres_medio_2 = []
        libres_otros = []
        
        for e in todos_los_espacios:
            # MAGIA: Excluir de los verdes si está reservado hoy
            if e in espacios_reservados_hoy:
                continue 
                
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
                        if sub == "NAN" or sub == "":
                            ocupa_todo = True
                        elif sub.endswith("1"):
                            ocupa_1 = True
                        elif sub.endswith("2"):
                            ocupa_2 = True
                        else:
                            ocupa_todo = True
                            
                    if ocupa_todo or (ocupa_1 and ocupa_2):
                        pass 
                    elif ocupa_2 and not ocupa_1:
                        libres_medio_1.append(e)
                    elif ocupa_1 and not ocupa_2:
                        libres_medio_2.append(e)

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

        # --- SECCIÓN DE RESERVAS ESPECIALES ACTUALIZADA (CERO SPAM) ---
        st.subheader("📌 Reservas Especiales del Día")
        if alertas_desplazamiento:
            for alerta in alertas_desplazamiento:
                if "⚠️" in alerta:
                    st.warning(alerta)
                else:
                    st.success(alerta)
        else: 
            st.info("No hay reservas programadas para este horario específico.")

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
