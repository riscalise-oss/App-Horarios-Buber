import streamlit as st
import pandas as pd
import base64
import os
import unicodedata
import re
from datetime import datetime, timedelta

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
# --- CONEXIÓN A GOOGLE SHEETS (LAZY LOADING Y CACHÉ) ---
# ==============================================================================
@st.cache_resource
def conectar_google():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credenciales = Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=scopes
        )
        return gspread.authorize(credenciales)
    except Exception as e:
        st.warning("⚠️ No se pudo conectar a Google. La función de reservar no estará disponible.")
        return None

# ==============================================================================
# --- FUNCIÓN PARA QUITAR TILDES ---
# ==============================================================================
def quitar_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                   if unicodedata.category(c) != 'Mn').upper().strip()

# ==============================================================================
# --- PROCESAMIENTO DE IMÁGENES OPTIMIZADO CON CACHÉ ---
# ==============================================================================
@st.cache_data
def cargar_imagen_base64(ruta_archivo):
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def aplicar_fondo_institucional(archivo_imagen):
    img_base64 = cargar_imagen_base64(archivo_imagen)
    if img_base64:
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

# --- TÍTULO CON LOGO OPTIMIZADO ---
img_logo_base64 = cargar_imagen_base64("logo.png")
if img_logo_base64:
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 20px; background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 10px;">
            <img src="data:image/png;base64,{img_logo_base64}" width="70" style="margin-right: 15px; border-radius: 8px;">
            <h1 style="margin: 0; padding: 0; color: #31333F;">Buscador de Ámbitos</h1>
        </div>
    """, unsafe_allow_html=True)
else:
    st.title("🛡️ Buscador de Ámbitos")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=300)
def cargar_datos():
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [quitar_tildes(c) for c in df_o.columns]
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    df_config = df_config.loc[:, ~df_config.columns.duplicated()].copy()
    
    # 🚀 MOTOR DE FECHAS Y FILTRADO 🚀
    col_fecha = None
    for col in df_config.columns:
        if df_config[col].astype(str).str.upper().str.contains("FECHA", na=False).any():
            col_fecha = col
            break
            
    if col_fecha is None and len(df_config.columns) > 5:
        if pd.to_datetime(df_config[5], errors='coerce', dayfirst=True).notna().sum() > 0:
            col_fecha = 5

    # FIX DE ZONA HORARIA ARGENTINA (-3)
    ahora_arg = datetime.utcnow() - timedelta(hours=3)
    hoy_ts = pd.Timestamp(ahora_arg.year, ahora_arg.month, ahora_arg.day)
    manana_ts = hoy_ts + pd.Timedelta(days=1)
    limite_2_semanas_ts = manana_ts + pd.Timedelta(days=14)

    if col_fecha is not None:
        df_config['TEMP_FECHA'] = pd.to_datetime(df_config[col_fecha], errors='coerce', dayfirst=True)
        mask = df_config['TEMP_FECHA'].isna() | (df_config['TEMP_FECHA'] >= hoy_ts)
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
            
    def procesar_y_guardar_aviso(texto_base, fecha_reserva):
        # Usamos .date() para una comparación a prueba de errores
        if pd.isna(fecha_reserva):
            if texto_base not in avisos["hoy"]: avisos["hoy"].append(texto_base)
        else:
            fecha_date = fecha_reserva.date()
            if fecha_date == hoy_ts.date():
                if texto_base not in avisos["hoy"]: avisos["hoy"].append(texto_base)
            elif fecha_date == manana_ts.date():
                if texto_base not in avisos["manana"]: avisos["manana"].append(texto_base)
            elif fecha_reserva <= limite_2_semanas_ts:
                fecha_str = fecha_reserva.strftime('%d/%m')
                texto_con_fecha = f"🗓️ **[{fecha_str}]** {texto_base}"
                if texto_con_fecha not in avisos["proximas"]: avisos["proximas"].append(texto_con_fecha)
            else:
                fecha_str = fecha_reserva.strftime('%d/%m')
                texto_con_fecha = f"🗓️ **[{fecha_str}]** {texto_base}"
                if texto_con_fecha not in avisos["futuras"]: avisos["futuras"].append(texto_con_fecha)

    # RECOLECTAMOS TODAS LAS RESERVAS SIN IMPORTAR SI TIENEN EMOJI O NO
    for idx, row in df_config.iterrows():
        fecha_val = row['TEMP_FECHA']
        texto_final = ""
        
        if col_avisos is not None:
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
        else:
            celdas_con_alerta = [str(x).strip() for x in row.tolist() if pd.notna(x) and ("⚠️" in str(x) or "🔴" in str(x) or "🟡" in str(x))]
            if celdas_con_alerta:
                texto_final = "   ".join(celdas_con_alerta)
            else:
                # Recolector generico de columnas 8 (espacio) y 9 (motivo) si falla lo anterior
                esp = str(row[8]).strip() if len(row) > 8 else ""
                mot = str(row[9]).strip() if len(row) > 9 else ""
                if esp and esp.upper() != "NAN" and esp.upper() != "ESPACIOS":
                    texto_final = esp
                    if mot and mot.upper() != "NAN":
                        texto_final += f" ({mot})"
        
        if texto_final:
            procesar_y_guardar_aviso(texto_final, fecha_val)
            lista_todas_reservas.append({'texto_base': texto_final, 'fecha': fecha_val, 'row': row})
        else:
            # Siempre se guarda en la memoria profunda para bloquear el cartel de HOY
            lista_todas_reservas.append({'texto_base': "Reserva de Espacio", 'fecha': fecha_val, 'row': row})

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
        
    return df_o, avisos, espacios, lista_todas_reservas

try:
    df_ocupados, avisos_agrupados, todos_los_espacios, lista_todas_reservas = cargar_datos()

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

        # =========================================================================
        # 🚀 AVISO INTELIGENTE "SOLO POR HOY" (ETIQUETA VISUAL) 🚀
        # =========================================================================
        # Usamos fechas estrictas .date() para que NUNCA falle la comparación
        ahora_arg_ts = datetime.utcnow() - timedelta(hours=3)
        hoy_date_estricto = ahora_arg_ts.date()
        
        mapa_dias = {'Monday': 'LUNES', 'Tuesday': 'MARTES', 'Wednesday': 'MIERCOLES', 'Thursday': 'JUEVES', 'Friday': 'VIERNES', 'Saturday': 'SABADO', 'Sunday': 'DOMINGO'}
        dia_hoy_str = mapa_dias.get(ahora_arg_ts.strftime('%A'), "").upper()
        dia_elegido_clean = quitar_tildes(dia_elegido)
        
        espacios_reservados_hoy = set()
        
        if dia_elegido_clean == dia_hoy_str:
            for res in lista_todas_reservas:
                fecha = res['fecha']
                # Verificación blindada: Compara estrictamente solo las fechas sin horarios
                if pd.notna(fecha) and fecha.date() == hoy_date_estricto:
                    row_data = res['row']
                    coincide_bloque = False
                    tiene_algun_bloque = False
                    
                    for val in row_data.tolist():
                        val_str = str(val).strip().upper()
                        numeros_en_celda = re.findall(r'\d+', val_str)
                        if str(bloque_elegido) in numeros_en_celda or f"BLOQUE {bloque_elegido}" in val_str or f"B{bloque_elegido}" in val_str:
                            coincide_bloque = True
                        if set(numeros_en_celda).intersection({"1", "2", "3", "4", "5", "6"}) or "BLOQUE" in val_str or "BLQ" in val_str:
                            tiene_algun_bloque = True
                            
                    if coincide_bloque or not tiene_algun_bloque:
                        for e in todos_los_espacios:
                            if any(e == str(x).strip().upper() for x in row_data.tolist()):
                                espacios_reservados_hoy.add(e)

        def formatear_espacio(e):
            if e in espacios_reservados_hoy:
                return f"**{e}** (🔴 HOY OCUPADO)"
            return e

        libres_completos_fmt = [formatear_espacio(e) for e in libres_completos]
        libres_medio_1_fmt = [formatear_espacio(e) for e in libres_medio_1]
        libres_medio_2_fmt = [formatear_espacio(e) for e in libres_medio_2]
        libres_otros_fmt = [formatear_espacio(e) for e in libres_otros]

        st.subheader("🟢 Ámbitos Libres")
        
        hay_libres = False
        if libres_completos:
            st.success("**Bloque Completo:**\n\n ✅ " + " | ✅ ".join(libres_completos_fmt))
            hay_libres = True
        if libres_medio_1:
            st.info("⏳ **1er Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(libres_medio_1_fmt))
            hay_libres = True
        if libres_medio_2:
            st.info("⏳ **2do Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(libres_medio_2_fmt))
            hay_libres = True
        if libres_otros:
            st.info("⏳ **Otros libres parciales:**\n\n ✔️ " + " | ✔️ ".join(libres_otros_fmt))
            hay_libres = True

        if not hay_libres:
            st.error("No hay espacios libres en este bloque.")
            
        if espacios_reservados_hoy:
            st.caption("💡 *Nota: Los espacios marcados con '(🔴 HOY OCUPADO)' suelen estar libres este día, pero tienen una reserva especial para la fecha de hoy. Podés usarlos para fechas futuras.*")

        st.divider()
        st.subheader("📌 Reservas Especiales")

        # =========================================================================
        # 🚀 RADAR ULTRA-INTELIGENTE 🚀
        # =========================================================================
        reservas_radar_cercanas = []
        reservas_radar_todas = []
        dia_buscado = quitar_tildes(dia_elegido)
        
        limite_2_sem_date = hoy_date_estricto + timedelta(days=15)
        
        for res in lista_todas_reservas:
            # Filtro visual para no sobrecargar si no tiene texto (se usa para bloqueo interno)
            if res['texto_base'] == "Reserva de Espacio":
                continue
                
            fecha = res['fecha']
            row_data = res['row']
            
            es_dia_buscado = False
            es_futura_o_hoy = False
            
            if pd.notna(fecha):
                if fecha.date() >= hoy_date_estricto:
                    es_futura_o_hoy = True
                    mapa_dias = {'Monday': 'LUNES', 'Tuesday': 'MARTES', 'Wednesday': 'MIERCOLES', 'Thursday': 'JUEVES', 'Friday': 'VIERNES'}
                    if mapa_dias.get(fecha.day_name()) == dia_buscado:
                        es_dia_buscado = True
            else:
                es_futura_o_hoy = True
                texto_fila = " ".join([str(x).upper() for x in row_data.tolist()])
                if dia_buscado in texto_fila:
                    es_dia_buscado = True
                    
            if es_futura_o_hoy and es_dia_buscado:
                coincide_bloque = False
                tiene_algun_bloque = False
                
                for val in row_data.tolist():
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
                            if fecha.date() <= limite_2_sem_date:
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
        # 🚀 FORMULARIO DE RESERVAS (LAZY LOADING) 🚀
        # =========================================================================
        st.divider()
        if st.toggle("📝 HACER UNA RESERVA ESPECIAL"):
            st.subheader("Registrar Nueva Reserva")
            
            with st.spinner("Estableciendo conexión segura con la base de datos..."):
                cliente = conectar_google()
                
            if cliente:
                try:
                    doc_conf = cliente.open("2026 ámbitos automatizado 2026")
                    hoja_conf = doc_conf.worksheet("Configuración")
                    lista_ambitos_dinamicos_form = [a for a in hoja_conf.col_values(7) if a and a.upper() not in ["ESPACIOS", "AMBITOS", "ÁMBITOS"]]
                    lista_ambitos_dinamicos_form = sorted(lista_ambitos_dinamicos_form)
                except Exception:
                    lista_ambitos_dinamicos_form = todos_los_espacios # Fallback si falla
                
                index_bloque = int(bloque_elegido) - 1 if str(bloque_elegido).isdigit() and int(bloque_elegido) in range(1, 7) else 0

                col_f1, col_f2 = st.columns([1, 2])
                fecha_input = col_f1.date_input("Fecha de la reserva")
                opciones_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_calculado = opciones_dias[fecha_input.weekday()]
                
                col_f2.markdown(f"<div style='margin-top: 32px; font-size: 16px;'>📅 Día: <b>{dia_calculado}</b></div>", unsafe_allow_html=True)

                st.caption("🔒 **Acceso restringido:** Ingresá tu nombre y clave una sola vez por sesión.")
                col_cred1, col_cred2 = st.columns(2)
                usuario_input = col_cred1.text_input("Tu Nombre", key="nombre_usuario", placeholder="Ej: Richard")
                clave_input = col_cred2.text_input("Clave de Autorización", type="password", key="clave_usuario")

                with st.form("formulario_reserva", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        bloques_input = st.multiselect(
                            "Bloque(s)", 
                            ["1", "2", "3", "4", "5", "6"], 
                            default=[str(index_bloque + 1)]
                        )
                    with col2:
                        espacio_input = st.selectbox("Espacio", lista_ambitos_dinamicos_form)
                        
                    motivo_input = st.text_input("Motivo (Ej: Acto 5to año)")
                    boton_guardar = st.form_submit_button("Guardar Reserva")

                if boton_guardar:
                    if clave_input != "Buber2026":
                        st.error("❌ Clave de autorización incorrecta. No tienes permiso para realizar reservas.")
                    elif not bloques_input:
                        st.warning("⚠️ Tenés que seleccionar al menos un bloque.")
                    elif motivo_input and usuario_input:
                        try:
                            hoja_libres = doc_conf.worksheet("Espacios Libres")
                            hoja_asignaciones = doc_conf.worksheet("Asignaciones") 
                            
                            datos_hoja = hoja_libres.get_all_values()
                            f_nueva = fecha_input.strftime("%d/%m/%Y")
                            e_nuevo = str(espacio_input).strip().upper()
                            
                            bloques_con_conflicto = []
                            for b_nuevo in bloques_input:
                                for fila in datos_hoja:
                                    if len(fila) >= 9:
                                        try:
                                            fecha_hoja = pd.to_datetime(str(fila[5]).strip(), dayfirst=True).date()
                                        except:
                                            fecha_hoja = None

                                        if fecha_hoja == fecha_input and str(fila[7]).strip() == str(b_nuevo).strip() and str(fila[8]).strip().upper() == e_nuevo:
                                            bloques_con_conflicto.append(b_nuevo)
                                            break
                            
                            if bloques_con_conflicto:
                                st.error(f"❌ Operación cancelada: El espacio {espacio_input} ya está reservado en los bloques: {', '.join(bloques_con_conflicto)}.")
                            else:
                                datos_asig = hoja_asignaciones.get_all_values()
                                profesores_desplazados = []
                                
                                for b_nuevo in bloques_input:
                                    for fila_asig in datos_asig[1:]: 
                                        if len(fila_asig) >= 6:
                                            dia_a = str(fila_asig[0]).strip().upper()
                                            blq_a = str(fila_asig[1]).strip().upper()
                                            esp_a = str(fila_asig[3]).strip().upper()
                                            
                                            if dia_a == dia_calculado.strip().upper() and blq_a == b_nuevo and esp_a == e_nuevo:
                                                materia_desplazada = str(fila_asig[4]).strip()
                                                profesor_desplazado = str(fila_asig[5]).strip()
                                                profesores_desplazados.append({
                                                    'profesor': profesor_desplazado, 
                                                    'materia': materia_desplazada,
                                                    'bloque': b_nuevo
                                                })
                                                break 
                                
                                ahora_str = (datetime.utcnow() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                audit_info = f"Registrado por: {usuario_input} el {ahora_str}"
                                
                                columna_f = hoja_libres.col_values(6) 
                                fila_inicial = len(columna_f) + 1
                                fila_final = fila_inicial + len(bloques_input) - 1
                                
                                valores_datos = []
                                valores_audit = []
                                for b_nuevo in bloques_input:
                                    valores_datos.append([f_nueva, dia_calculado, int(b_nuevo), espacio_input, motivo_input])
                                    valores_audit.append([audit_info])

                                hoja_libres.update(range_name=f"F{fila_inicial}:J{fila_final}", values=valores_datos, value_input_option='USER_ENTERED')
                                hoja_libres.update(range_name=f"L{fila_inicial}:L{fila_final}", values=valores_audit, value_input_option='USER_ENTERED')

                                resumen_bloques = ", ".join(bloques_input)
                                resumen = f"**{dia_calculado} {f_nueva}** | Bloques **{resumen_bloques}** | **{espacio_input}** ({motivo_input})"
                                
                                st.session_state['ultima_fila_inicio'] = fila_inicial
                                st.session_state['ultima_fila_fin'] = fila_final
                                st.session_state['ultimo_resumen'] = resumen
                                st.session_state['reubicacion_resuelta'] = False
                                
                                st.session_state['reserva_datos'] = {
                                    'fecha': f_nueva,
                                    'dia': dia_calculado,
                                    'bloques': bloques_input
                                }
                                
                                if profesores_desplazados:
                                    st.session_state['profes_desplazados'] = profesores_desplazados
                                    mensajes_profes = "\n".join([f"👉 **{p['profesor']}** ({p['materia']}) en el Bloque {p['bloque']}" for p in profesores_desplazados])
                                    st.warning(f"⚠️ **¡Reservas guardadas!** Pero atención, desplazaste a:\n\n{mensajes_profes}\n\n📍 {resumen}")
                                else:
                                    st.session_state['profes_desplazados'] = []
                                    st.success(f"✅ ¡Reservas guardadas con éxito! No se desplazó a ningún profesor.\n\n👉 {resumen}")
                                    st.balloons()
                                
                                st.cache_data.clear()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                    else:
                        st.warning("⚠️ Completá tu Nombre y el Motivo antes de guardar.")

        # =========================================================================
        # 🚀 SISTEMA "DESHACER" Y "REUBICAR" ACTUALIZADO
        # =========================================================================
        if 'ultima_fila_inicio' in st.session_state:
            st.divider()
            cliente = conectar_google() 
            if cliente:
                st.info(f"🔄 **Última reserva realizada por vos:** {st.session_state['ultimo_resumen']}")
                if st.button("⚠️ Me equivoqué, cancelar estas reservas", type="primary"):
                    try:
                        doc_borrar = cliente.open("2026 ámbitos automatizado 2026")
                        hoja_borrar = doc_borrar.worksheet("Espacios Libres")
                        
                        fila_ini = st.session_state['ultima_fila_inicio']
                        fila_fin = st.session_state['ultima_fila_fin']
                        num_filas = fila_fin - fila_ini + 1
                        
                        filas_vacias = [["", "", "", "", ""] for _ in range(num_filas)]
                        filas_vacias_audit = [[""] for _ in range(num_filas)]
                        
                        hoja_borrar.update(range_name=f"F{fila_ini}:J{fila_fin}", values=filas_vacias, value_input_option='USER_ENTERED')
                        hoja_borrar.update(range_name=f"L{fila_ini}:L{fila_fin}", values=filas_vacias_audit, value_input_option='USER_ENTERED')
                        
                        if 'filas_reubicacion' in st.session_state:
                            for fila_reub in st.session_state['filas_reubicacion']:
                                hoja_borrar.update(range_name=f"F{fila_reub}:J{fila_reub}", values=[["", "", "", "", ""]], value_input_option='USER_ENTERED')
                                hoja_borrar.update(range_name=f"L{fila_reub}", values=[[""]], value_input_option='USER_ENTERED')
                            mensaje_extra = " y las reubicaciones"
                        else:
                            mensaje_extra = ""
                        
                        st.success(f"🗑️ ¡Las reservas{mensaje_extra} fueron anuladas! El sistema quedó limpio.")
                        
                        for clave in ['ultima_fila_inicio', 'ultima_fila_fin', 'ultimo_resumen', 'profes_desplazados', 'reubicacion_resuelta', 'reserva_datos', 'filas_reubicacion']:
                            if clave in st.session_state:
                                del st.session_state[clave]
                        
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al cancelar la reserva: {e}")

                if st.session_state.get('profes_desplazados') and not st.session_state.get('reubicacion_resuelta', False):
                    st.divider()
                    st.subheader("📍 Reubicar profesores desplazados")
                    
                    with st.form("form_reubicacion_multiple"):
                        selecciones_reub = []
                        opciones_libres = ["Seleccionar un espacio..."] + libres_completos
                        
                        for p in st.session_state['profes_desplazados']:
                            st.write(f"**{p['profesor']}** ({p['materia']}) - Bloque {p['bloque']}")
                            esp = st.selectbox(f"Nuevo ámbito para {p['profesor']}:", opciones_libres, key=f"reub_{p['profesor']}_{p['bloque']}")
                            selecciones_reub.append({'profesor': p['profesor'], 'bloque': p['bloque'], 'espacio': esp})
                            
                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            btn_confirmar = st.form_submit_button("✅ Confirmar Reubicaciones", type="primary", use_container_width=True)
                        with col_r2:
                            btn_hablar = st.form_submit_button("🗣️ Hablaré con los profesores", use_container_width=True)
                            
                    if btn_confirmar:
                        if all(s['espacio'] != "Seleccionar un espacio..." for s in selecciones_reub):
                            try:
                                doc_r = cliente.open("2026 ámbitos automatizado 2026")
                                hoja_r = doc_r.worksheet("Espacios Libres")
                                datos_r = st.session_state['reserva_datos']
                                ahora_r = datetime.utcnow() - timedelta(hours=3)
                                audit_r = f"Reubicado por: {usuario_input} el {ahora_r.strftime('%d/%m/%Y %H:%M:%S')}"
                                
                                filas_reubicadas = []
                                for s in selecciones_reub:
                                    siguiente_fila_r = len(hoja_r.col_values(6)) + 1
                                    motivo_r = f"Reubicación de {s['profesor']}"
                                    hoja_r.update(range_name=f"F{siguiente_fila_r}:J{siguiente_fila_r}", 
                                                  values=[[datos_r['fecha'], datos_r['dia'], int(s['bloque']), s['espacio'], motivo_r]], 
                                                  value_input_option='USER_ENTERED')
                                    hoja_r.update(range_name=f"L{siguiente_fila_r}", values=[[audit_r]], value_input_option='USER_ENTERED')
                                    filas_reubicadas.append(siguiente_fila_r)
                                    
                                st.session_state['filas_reubicacion'] = filas_reubicadas
                                st.session_state['reubicacion_resuelta'] = True
                                st.success("¡Listo! Todos los profesores fueron reubicados exitosamente.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar reubicación: {e}")
                        else:
                            st.warning("⚠️ Tenés que asignarle un espacio a cada profesor antes de confirmar, o elegir hablar con ellos.")
                            
                    if btn_hablar:
                        st.session_state['reubicacion_resuelta'] = True
                        st.rerun()

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

# --- PIE DE PÁGINA ---
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: grey; padding: 10px; background-color: transparent; z-index: 100; }
    </style>
    <div class="footer">by Richard</div>
""", unsafe_allow_html=True)
