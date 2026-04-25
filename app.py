import streamlit as st
import pandas as pd
import base64
import os
import unicodedata
import re
from datetime import datetime

# --- NUEVAS LIBRERÍAS PARA GOOGLE SHEETS ---
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")

# =========================================================================
# 🎨 OCULTAR MENÚ DE STREAMLIT Y GITHUB
# =========================================================================
ocultar_menu_estilo = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(ocultar_menu_estilo, unsafe_allow_html=True)

# ==============================================================================
# --- CONEXIÓN A GOOGLE SHEETS ---
# ==============================================================================
try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credenciales = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    cliente = gspread.authorize(credenciales)
except Exception as e:
    st.warning("⚠️ Todavía no se configuraron los secretos de Google. La función de reservar no estará disponible.")

# ==============================================================================
# --- FUNCIÓN PARA QUITAR TILDES ---
# ==============================================================================
def quitar_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                   if unicodedata.category(c) != 'Mn').upper().strip()

# ==============================================================================
# --- FUNCIÓN PARA EL FONDO INSTITUCIONAL ---
# ==============================================================================
def aplicar_fondo_institucional(archivo_imagen):
    if os.path.exists(archivo_imagen):
        try:
            with open(archivo_imagen, "rb") as f:
                data = f.read()
            img_base64 = base64.b64encode(data).decode()
            
            page_bg_img = f'''
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{img_base64}");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            '''
            st.markdown(page_bg_img, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error al cargar el fondo: {e}")
    else:
        pass 

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
    df_o.columns = [quitar_tildes(c) for c in df_o.columns]
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    df_config = df_config.loc[:, ~df_config.columns.duplicated()].copy()
    
    # --- NUEVO: CARGAR ÁMBITOS DINÁMICOS DESDE COLUMNA G ---
    try:
        doc = cliente.open("2026 ámbitos automatizado 2026")
        hoja_conf = doc.worksheet("Configuración")
        lista_ambitos_dinamicos = [a for a in hoja_conf.col_values(7) if a and a.upper() not in ["ESPACIOS", "AMBITOS", "ÁMBITOS"]]
        lista_ambitos_dinamicos = sorted(lista_ambitos_dinamicos)
    except Exception:
        lista_ambitos_dinamicos = [] # Fallback si falla
    
    # 🚀 MOTOR DE FECHAS Y FILTRADO 🚀
    col_fecha = None
    for col in df_config.columns:
        if df_config[col].astype(str).str.upper().str.contains("FECHA", na=False).any():
            col_fecha = col
            break
            
    if col_fecha is None and len(df_config.columns) > 5:
        if pd.to_datetime(df_config[5], errors='coerce', dayfirst=True).notna().sum() > 0:
            col_fecha = 5

    hoy = pd.Timestamp('today').normalize()
    manana = hoy + pd.Timedelta(days=1)
    limite_2_semanas = manana + pd.Timedelta(days=14)

    if col_fecha is not None:
        df_config['TEMP_FECHA'] = pd.to_datetime(df_config[col_fecha], errors='coerce', dayfirst=True)
        mask = df_config['TEMP_FECHA'].isna() | (df_config['TEMP_FECHA'] >= hoy)
        df_config = df_config[mask]
        df_config = df_config.sort_values(by='TEMP_FECHA', na_position='first')
    else:
        df_config['TEMP_FECHA'] = pd.NaT

    avisos = {"hoy": [], "manana": [], "proximas": [], "futuras": []}
    lista_todas_reservas = [] 
    
    col_avisos = None
    col_desplaza = None
    col_motivo = None
    
    for col in df_config.columns:
        col_str = df_config[col].astype(str)
        if col_str.str.contains("Espacios Bloqueados", case=False, na=False).any():
            col_avisos = col
        if col_str.str.contains("Avisar al Profesor", case=False, na=False).any() or \
           col_str.str.contains("Desplaza a:", case=False, na=False).any():
            col_desplaza = col
        if col_str.str.contains("MOTIVO", case=False, na=False).any():
            col_motivo = col
            
    def procesar_y_guardar_aviso(texto_base, fecha_reserva, row_data):
        if pd.isna(fecha_reserva) or fecha_reserva == hoy:
            if texto_base not in avisos["hoy"]: avisos["hoy"].append(texto_base)
        elif fecha_reserva == manana:
            if texto_base not in avisos["manana"]: avisos["manana"].append(texto_base)
        elif fecha_reserva <= limite_2_semanas:
            fecha_str = fecha_reserva.strftime('%d/%m')
            texto_con_fecha = f"🗓️ **[{fecha_str}]** {texto_base}"
            if texto_con_fecha not in avisos["proximas"]: avisos["proximas"].append(texto_con_fecha)
        else:
            fecha_str = fecha_reserva.strftime('%d/%m')
            texto_con_fecha = f"🗓️ **[{fecha_str}]** {texto_base}"
            if texto_con_fecha not in avisos["futuras"]: avisos["futuras"].append(texto_con_fecha)
            
        lista_todas_reservas.append({
            'texto_base': texto_base,
            'fecha': fecha_reserva,
            'row': row_data
        })

    if col_avisos is not None:
        for idx, row in df_config.iterrows():
            aviso_ppal = str(row[col_avisos]).strip()
            
            if aviso_ppal and aviso_ppal.upper() not in ["", "NAN", "NAT", "ESPACIOS BLOQUEADOS / RESERVADOS", "ESPACIOS BLOQUEADOS"]:
                texto_final = aviso_ppal
                
                if col_motivo is not None:
                    aviso_motivo = str(row[col_motivo]).strip()
                    if aviso_motivo and aviso_motivo.upper() not in ["", "NAN", "NAT", "MOTIVO", "NONE"]:
                        texto_final += f" 👉 *Motivo: {aviso_motivo}*"
                
                if col_desplaza is not None:
                    aviso_profe = str(row[col_desplaza]).strip()
                    if aviso_profe and aviso_profe.upper() not in ["", "NAN", "NAT", "AVISAR AL PROFESOR", "#N/A", "#REF!", "NONE"]:
                        texto_final += f"   {aviso_profe}"
                        
                procesar_y_guardar_aviso(texto_final, row['TEMP_FECHA'], row)
    else:
        for idx, row in df_config.iterrows():
            celdas_con_alerta = [str(x).strip() for x in row.values if pd.notna(x) and ("⚠️" in str(x) or "🔴" in str(x) or "🟡" in str(x))]
            if celdas_con_alerta:
                texto_unido = "   ".join(celdas_con_alerta)
                procesar_y_guardar_aviso(texto_unido, row['TEMP_FECHA'], row)

    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).map(quitar_tildes)
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "JUEVES": 4, "VIERNES": 5}
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
        
    # Si la lectura dinámica falló por algo, usamos los espacios del csv
    if not lista_ambitos_dinamicos:
        lista_ambitos_dinamicos = espacios

    return df_o, avisos, espacios, lista_todas_reservas, lista_ambitos_dinamicos

try:
    df_ocupados, avisos_agrupados, todos_los_espacios, lista_todas_reservas, lista_ambitos_dinamicos = cargar_datos()

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
                        sub_texto = str(sub) 
                        
                        if sub_texto == "NAN" or sub_texto == "": ocupa_todo = True
                        elif sub_texto.endswith("1"): ocupa_1 = True
                        elif sub_texto.endswith("2"): ocupa_2 = True
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

        st.divider()
        st.subheader("📌 Reservas Especiales")

        # =========================================================================
        # 🚀 RADAR ULTRA-INTELIGENTE 🚀
        # =========================================================================
        reservas_radar_cercanas = []
        reservas_radar_todas = []
        dia_buscado = quitar_tildes(dia_elegido)
        hoy_ts = pd.Timestamp('today').normalize()
        limite_2_sem_ts = hoy_ts + pd.Timedelta(days=15)
        
        for res in lista_todas_reservas:
            fecha = res['fecha']
            row_data = res['row']
            
            es_dia_buscado = False
            es_futura_o_hoy = False
            
            if pd.notna(fecha):
                if fecha >= hoy_ts:
                    es_futura_o_hoy = True
                    mapa_dias = {'Monday': 'LUNES', 'Tuesday': 'MARTES', 'Wednesday': 'MIERCOLES', 'Thursday': 'JUEVES', 'Friday': 'VIERNES'}
                    if mapa_dias.get(fecha.day_name()) == dia_buscado:
                        es_dia_buscado = True
            else:
                es_futura_o_hoy = True
                texto_fila = " ".join([str(x).upper() for x in row_data.values])
                if dia_buscado in texto_fila:
                    es_dia_buscado = True
                    
            if es_futura_o_hoy and es_dia_buscado:
                coincide_bloque = False
                tiene_algun_bloque = False
                
                for val in row_data.values:
                    val_str = str(val).strip().upper()
                    numeros_en_celda = re.findall(r'\d+', val_str)
                    
                    if str(bloque_elegido) in numeros_en_celda or f"BLOQUE {bloque_elegido}" in val_str or f"B{bloque_elegido}" in val_str:
                        coincide_bloque = True
                        
                    if set(numeros_en_celda).intersection({"1", "2", "3", "4", "5", "6"}) or "BLOQUE" in val_str or "BLQ" in val_str:
                        tiene_algun_bloque = True
                        
                if coincide_bloque or not tiene_algun_bloque:
                    if pd.notna(fecha):
                        fecha_str_corta = fecha.strftime('%d/%m')
                        fecha_str_larga = fecha.strftime('%d/%m/%Y')
                        
                        texto_largo = f"🎯 **[{fecha_str_larga}]** {res['texto_base']}"
                        texto_corto = f"🎯 **[{fecha_str_corta}]** {res['texto_base']}"
                        
                        if texto_largo not in reservas_radar_todas:
                            reservas_radar_todas.append(texto_largo)
                            if fecha <= limite_2_sem_ts:
                                reservas_radar_cercanas.append(texto_corto)
                    else:
                        texto_generico = f"🎯 **[Frecuente/Día Completo]** {res['texto_base']}"
                        if texto_generico not in reservas_radar_todas:
                            reservas_radar_todas.append(texto_generico)
                            reservas_radar_cercanas.append(texto_generico)

        if avisos_agrupados["hoy"]:
            st.warning("**📍 HOY:**\n\n" + "\n\n".join([f"**•** {a}" for a in avisos_agrupados["hoy"]]))
        else:
            st.success("**📍 HOY:** No hay reservas especiales generales.")

        if avisos_agrupados["manana"]:
            st.info("**⏭️ MAÑANA:**\n\n" + "\n\n".join([f"**•** {a}" for a in avisos_agrupados["manana"]]))

        if reservas_radar_cercanas:
            st.error(f"🚨 **ATENCIÓN: Hay reservas próximas para los {dia_elegido} en este bloque:**\n\n" + "\n\n".join([f"**•** {a}" for a in reservas_radar_cercanas]))
            
        if reservas_radar_todas:
            with st.expander(f"🔮 Ver TODAS las reservas para {dia_elegido} - Bloque {bloque_elegido} ({len(reservas_radar_todas)} en total)", expanded=False):
                st.write("\n\n".join([f"**•** {a}" for a in reservas_radar_todas]))

        with st.expander("📅 Ver TODAS las reservas generales de las próximas 2 semanas", expanded=False):
            if avisos_agrupados["proximas"]:
                st.write("\n\n".join([f"**•** {a}" for a in avisos_agrupados["proximas"]]))
            else:
                st.write("No hay otras reservas a corto plazo.")

        if avisos_agrupados["futuras"]:
            with st.expander("📂 Ver reservas a largo plazo generales (después de 2 semanas)", expanded=False):
                st.write("\n\n".join([f"**•** {a}" for a in avisos_agrupados["futuras"]]))

        st.divider()

        with st.expander("🔴 Ver Clases Regulares", expanded=False):
            if not ocu.empty:
                if 'BLOQUE' in ocu.columns:
                    ocu['BLOQUE'] = ocu['BLOQUE'].astype(str).replace(traductor_bloques)
                    
                cols = [c for c in ['BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA'] if c in ocu.columns]
                st.dataframe(ocu[cols], hide_index=True, use_container_width=True)

        # =========================================================================
        # 🚀 FORMULARIO DE RESERVAS (CON PROTECCIÓN Y DESHACER) 🚀
        # =========================================================================
        st.divider()
        st.subheader("📝 Registrar Nueva Reserva")
        
        index_bloque = int(bloque_elegido) - 1 if str(bloque_elegido).isdigit() and int(bloque_elegido) in range(1, 7) else 0

        # --- 1. FECHA Y DÍA (Juntos y alineados) ---
        col_f1, col_f2 = st.columns([1, 2])
        fecha_input = col_f1.date_input("Fecha de la reserva")
        opciones_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_calculado = opciones_dias[fecha_input.weekday()]
        # Truco HTML para empujar el texto para abajo y que quede alineado con la cajita de fecha
        col_f2.markdown(f"<div style='margin-top: 32px; font-size: 16px;'>📅 Día: <b>{dia_calculado}</b></div>", unsafe_allow_html=True)

        # --- 2. CREDENCIALES (Afuera para que no se borren) ---
        st.caption("🔒 **Acceso restringido:** Ingresá tu nombre y clave una sola vez por sesión.")
        col_cred1, col_cred2 = st.columns(2)
        usuario_input = col_cred1.text_input("Tu Nombre", key="nombre_usuario", placeholder="Ej: Richard")
        clave_input = col_cred2.text_input("Clave de Autorización", type="password", key="clave_usuario")

        # --- 3. FORMULARIO PRINCIPAL (Con memoria para Reubicación) ---
        motivo_predefinido = st.session_state.get('motivo_reubicacion', '')
