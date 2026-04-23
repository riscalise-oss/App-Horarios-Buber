import streamlit as st
import pandas as pd
import base64
import os
import unicodedata
import re
from datetime import datetime

# --- LIBRERÍAS PARA GOOGLE SHEETS ---
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos - ADMIN", page_icon="logo.png", layout="wide")

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
# --- SISTEMA DE LOGIN ---
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: rgba(255,255,255,0.7); border-radius: 10px;">
            <h2>🔐 Acceso Administrador</h2>
        </div>
    """, unsafe_allow_html=True)
    
    password_input = st.text_input("Ingresa la clave de acceso:", type="password")
    if st.button("Entrar"):
        if password_input == "Buber2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    return False

if not check_password():
    st.stop()

# ==============================================================================
# --- FUNCIONES AUXILIARES (Tus originales) ---
# ==============================================================================
def quitar_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                   if unicodedata.category(c) != 'Mn').upper().strip()

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
        except Exception: pass

# --- CSS LIMPIO ---
st.markdown("<style>footer {visibility: hidden !important;} #MainMenu {visibility: hidden !important;}</style>", unsafe_allow_html=True)
aplicar_fondo_institucional("fondo.png")

traductor_bloques = {
    "1": "1. 7:40 a 9:00", "2": "2. 9:10 a 10:30", "3": "3. 10:45 a 12:05",
    "4": "4. 12:15 a 13:35", "5": "5. 13:45 a 15:00", "6": "6. 15:10 a 16:30"
}

# --- TÍTULO ---
try:
    with open("logo.png", "rb") as f:
        data = f.read()
    img_b64 = base64.b64encode(data).decode()
    st.markdown(f'<div style="display: flex; align-items: center; margin-bottom: 20px; background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 10px;"><img src="data:image/png;base64,{img_b64}" width="70" style="margin-right: 15px; border-radius: 8px;"><h1 style="margin: 0; color: #31333F;">Buscador de Ámbitos</h1></div>', unsafe_allow_html=True)
except Exception:
    st.title("🛡️ Buscador de Ámbitos")

# ==============================================================================
# --- CARGA DE DATOS (CRONOGRAMA + LISTA DINÁMICA DE CONFIGURACIÓN) ---
# ==============================================================================
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [quitar_tildes(c) for c in df_o.columns]
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    df_config = df_config.loc[:, ~df_config.columns.duplicated()].copy()

    # --- LISTA DINÁMICA DESDE HOJA "CONFIGURACIÓN" (Columna G) ---
    try:
        doc_madre = cliente.open("2026 ámbitos automatizado 2026")
        hoja_conf = doc_madre.worksheet("Configuración")
        lista_g = hoja_conf.col_values(7) # Columna G
        espacios_dinamicos = sorted([a for a in lista_g if a and a.upper() not in ["ESPACIOS", "AMBITOS", "ÁMBITOS", "ÁMBITO"]])
    except:
        espacios_dinamicos = ["7º 13", "7º 14", "Error al cargar"]

    # --- TU MOTOR DE FECHAS Y RADAR (Intacto) ---
    col_fecha = None
    for col in df_config.columns:
        if df_config[col].astype(str).str.upper().str.contains("FECHA", na=False).any():
            col_fecha = col
            break
    if col_fecha is None and len(df_config.columns) > 5:
        if pd.to_datetime(df_config[5], errors='coerce', dayfirst=True).notna().sum() > 0: col_fecha = 5

    hoy = pd.Timestamp('today').normalize()
    manana = hoy + pd.Timedelta(days=1)
    limite_2_semanas = manana + pd.Timedelta(days=14)

    if col_fecha is not None:
        df_config['TEMP_FECHA'] = pd.to_datetime(df_config[col_fecha], errors='coerce', dayfirst=True)
        mask = df_config['TEMP_FECHA'].isna() | (df_config['TEMP_FECHA'] >= hoy)
        df_config = df_config[mask].sort_values(by='TEMP_FECHA', na_position='first')
    else:
        df_config['TEMP_FECHA'] = pd.NaT

    avisos = {"hoy": [], "manana": [], "proximas": [], "futuras": []}
    lista_todas_reservas = [] 
    
    col_avisos, col_desplaza, col_motivo = None, None, None
    for col in df_config.columns:
        col_str = df_config[col].astype(str)
        if col_str.str.contains("Espacios Bloqueados", case=False, na=False).any(): col_avisos = col
        if col_str.str.contains("Avisar al Profesor", case=False, na=False).any() or col_str.str.contains("Desplaza a:", case=False, na=False).any(): col_desplaza = col
        if col_str.str.contains("MOTIVO", case=False, na=False).any(): col_motivo = col

    def procesar_y_guardar_aviso(texto_base, fecha_reserva, row_data):
        if pd.isna(fecha_reserva) or fecha_reserva == hoy:
            if texto_base not in avisos["hoy"]: avisos["hoy"].append(texto_base)
        elif fecha_reserva == manana:
            if texto_base not in avisos["manana"]: avisos["manana"].append(texto_base)
        elif fecha_reserva <= limite_2_semanas:
            txt = f"🗓️ **[{fecha_reserva.strftime('%d/%m')}]** {texto_base}"
            if txt not in avisos["proximas"]: avisos["proximas"].append(txt)
        else:
            txt = f"🗓️ **[{fecha_reserva.strftime('%d/%m')}]** {texto_base}"
            if txt not in avisos["futuras"]: avisos["futuras"].append(txt)
        lista_todas_reservas.append({'texto_base': texto_base, 'fecha': fecha_reserva, 'row': row_data})

    if col_avisos is not None:
        for idx, row in df_config.iterrows():
            aviso_ppal = str(row[col_avisos]).strip()
            if aviso_ppal and aviso_ppal.upper() not in ["", "NAN", "NAT", "ESPACIOS BLOQUEADOS / RESERVADOS", "ESPACIOS BLOQUEADOS"]:
                texto_final = aviso_ppal
                if col_motivo is not None:
                    m = str(row[col_motivo]).strip()
                    if m and m.upper() not in ["", "NAN", "NAT", "MOTIVO", "NONE"]: texto_final += f" 👉 *Motivo: {m}*"
                if col_desplaza is not None:
                    d = str(row[col_desplaza]).strip()
                    if d and d.upper() not in ["", "NAN", "NAT", "AVISAR AL PROFESOR", "#N/A", "#REF!", "NONE"]: texto_final += f"   {d}"
                procesar_y_guardar_aviso(texto_final, row['TEMP_FECHA'], row)
    else:
        for idx, row in df_config.iterrows():
            celdas = [str(x).strip() for x in row.values if pd.notna(x) and any(e in str(x) for e in ["⚠️", "🔴", "🟡"])]
            if celdas: procesar_y_guardar_aviso("   ".join(celdas), row['TEMP_FECHA'], row)

    # --- NORMALIZACIÓN DE DF_OCUPADOS ---
    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).map(quitar_tildes)
        df_o['ORDEN_DIA'] = df_o['DIA'].map({"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "JUEVES": 4, "VIERNES": 5})
    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        df_o['ORDEN_BLOQUE'] = pd.to_numeric(df_o['BLOQUE'], errors='coerce').fillna(99)
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()
    if 'SUBBLOQUE' in df_o.columns:
        df_o['SUBBLOQUE'] = df_o['SUBBLOQUE'].astype(str).str.strip().str.upper().replace('NAN', '')

    return df_o, avisos, espacios_dinamicos, lista_todas_reservas

try:
    df_ocupados, avisos_agrupados, todos_los_espacios, lista_todas_reservas = cargar_datos()
    tab1, tab2, tab3 = st.tabs(["🕰️ Buscar por Horario", "👤 Buscar Docente/Curso", "📍 Buscar por Ámbito"])

    with tab1:
        col_dia, col_bloque = st.columns(2)
        dias_disponibles = df_ocupados.sort_values('ORDEN_DIA')['DIA'].dropna().unique().tolist()
        dia_elegido = col_dia.selectbox("📅 Día:", dias_disponibles)
        bloques_raw = df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique()
        bloques_ordenados = sorted([b for b in bloques_raw if b != "NAN"], key=lambda x: int(x) if x.isdigit() else x)
        bloque_elegido = col_bloque.selectbox("⏰ Bloque:", bloques_ordenados, format_func=lambda x: traductor_bloques.get(str(x), f"Bloque {x}"))

        st.divider()
        st.header(f"{dia_elegido} - {traductor_bloques.get(str(bloque_elegido), f'Bloque {bloque_elegido}')}")

        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))].copy()
        
        # --- TU LÓGICA DE ESPACIOS LIBRES (Intacta) ---
        libres_completos, libres_medio_1, libres_medio_2 = [], [], []
        for e in todos_los_espacios:
            df_esp = ocu[ocu['ESPACIOS'] == e.upper()]
            if df_esp.empty: libres_completos.append(e)
            else:
                df_clases = df_esp[~df_esp.astype(str).apply(lambda row: row.str.contains('ALMUERZO', case=False)).any(axis=1)]
                if df_clases.empty: libres_completos.append(e)
                else:
                    o1, o2, ot = False, False, False
                    for sub in df_clases['SUBBLOQUE'].astype(str).str.strip().str.upper():
                        if sub in ["NAN", ""]: ot = True
                        elif sub.endswith("1"): o1 = True
                        elif sub.endswith("2"): o2 = True
                        else: ot = True
                    if not (ot or (o1 and o2)):
                        if o2 and not o1: libres_medio_1.append(e)
                        elif o1 and not o2: libres_medio_2.append(e)

        st.subheader("🟢 Ámbitos Libres")
        if libres_completos: st.success("**Bloque Completo:**\n\n ✅ " + " | ✅ ".join(sorted(libres_completos)))
        if libres_medio_1: st.info("⏳ **1er Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(sorted(libres_medio_1)))
        if libres_medio_2: st.info("⏳ **2do Medio Bloque:**\n\n ✔️ " + " | ✔️ ".join(sorted(libres_medio_2)))

        st.divider()
        st.subheader("📌 Reservas Especiales (Radar)")
        
        # --- TU RADAR ULTRA-INTELIGENTE (Intacto) ---
        res_radar_cercanas, res_radar_todas = [], []
        dia_buscado = quitar_tildes(dia_elegido)
        hoy_ts = pd.Timestamp('today').normalize()
        limite_2_sem_ts = hoy_ts + pd.Timedelta(days=15)
        
        for res in lista_todas_reservas:
            fecha, row_data = res['fecha'], res['row']
            es_dia, es_futuro = False, False
            if pd.notna(fecha):
                if fecha >= hoy_ts:
                    es_futuro = True
                    mapa = {'Monday': 'LUNES', 'Tuesday': 'MARTES', 'Wednesday': 'MIERCOLES', 'Thursday': 'JUEVES', 'Friday': 'VIERNES'}
                    if mapa.get(fecha.day_name()) == dia_buscado: es_dia = True
            else:
                es_futuro = True
                if dia_buscado in " ".join([str(x).upper() for x in row_data.values]): es_dia = True
            
            if es_futuro and es_dia:
                coincide, tiene_bloque = False, False
                for val in row_data.values:
                    v_str = str(val).strip().upper()
                    nums = re.findall(r'\d+', v_str)
                    if str(bloque_elegido) in nums or f"BLOQUE {bloque_elegido}" in v_str: coincide = True
                    if set(nums).intersection({"1","2","3","4","5","6"}) or "BLOQUE" in v_str: tiene_bloque = True
                
                if coincide or not tiene_bloque:
                    txt = res['texto_base']
                    if pd.notna(fecha):
                        res_radar_todas.append(f"🎯 **[{fecha.strftime('%d/%m/%Y')}]** {txt}")
                        if fecha <= limite_2_sem_ts: res_radar_cercanas.append(f"🎯 **[{fecha.strftime('%d/%m')}]** {txt}")
                    else:
                        res_radar_todas.append(f"🎯 **[Frecuente]** {txt}")
                        res_radar_cercanas.append(f"🎯 **[Frecuente]** {txt}")

        if avisos_agrupados["hoy"]: st.warning("**📍 HOY:**\n\n" + "\n\n".join([f"**•** {a}" for a in avisos_agrupados["hoy"]]))
        if res_radar_cercanas: st.error(f"🚨 **RESERVAS PRÓXIMAS {dia_elegido} B{bloque_elegido}:**\n\n" + "\n\n".join([f"**•** {a}" for a in res_radar_cercanas]))

        # =========================================================================
        # 🚀 FORMULARIO DE RESERVAS (NUEVO: AUDITORÍA + SIN CARTEL)
        # =========================================================================
        st.divider()
        st.subheader("📝 Registrar Nueva Reserva")
        
        fecha_input = st.date_input("Fecha de la reserva")
        op_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_calc = op_dias[fecha_input.weekday()]
        
        with st.form("formulario_reserva", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                idx_b = int(bloque_elegido)-1 if str(bloque_elegido).isdigit() else 0
                bloque_in = st.selectbox("Bloque", ["1", "2", "3", "4", "5", "6"], index=idx_b)
                usuario_in = st.text_input("Tu Nombre / Identificación", placeholder="Ej: Richard")
            with col2:
                espacio_in = st.selectbox("Espacio", todos_los_espacios)
                motivo_in = st.text_input("Motivo (Ej: Acto 5to año)")
            with col3:
                st.info(f"📅 Día: **{dia_calc}**")
                st.write("Se registrará nombre, fecha y hora.")
            
            boton_guardar = st.form_submit_button("💾 Guardar Reserva")

        if boton_guardar:
            if motivo_in and usuario_in:
                try:
                    doc = cliente.open("2026 ámbitos automatizado 2026")
                    hoja = doc.worksheet("Espacios Libres")
                    f_nueva = fecha_input.strftime("%d/%m/%Y")
                    
                    # Choques
                    ya_existe = any(f[5]==f_nueva and str(f[7])==str(bloque_in) and f[8].strip().upper()==espacio_in.upper() for f in hoja.get_all_values() if len(f)>=9)
                    
                    if ya_existe:
                        st.error(f"❌ {espacio_in} ya está reservado para esa fecha/bloque.")
                    else:
                        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                        audit_info = f"Registrado por: {usuario_in} el {ahora}"
                        
                        prox = len(hoja.col_values(6)) + 1
                        # Escribimos de F a K (K es la columna 11 para la auditoría)
                        rango = f"F{prox}:K{prox}"
                        valores = [[f_nueva, dia_calc, int(bloque_in), espacio_in, motivo_in, audit_info]]
                        
                        hoja.update(range_name=rango, values=valores, value_input_option='USER_ENTERED')
                        st.success("✅ ¡Reserva guardada con éxito!")
                        st.balloons()
                        st.cache_data.clear()
                except Exception as e: st.error(f"Error al guardar: {e}")
            else: st.warning("⚠️ Completá tu nombre y el motivo.")

    # --- PESTAÑAS 2 Y 3 (Tus originales, intactas) ---
    with tab2:
        tipo = st.radio("Buscar por:", ["Docente", "Curso"], horizontal=True)
        col_f = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col_f].dropna().unique() if str(x).upper() != "NAN"])
        sel = st.selectbox(f"Selecciona {tipo}:", lista)
        st.divider()
        res = df_ocupados[df_ocupados[col_f] == sel].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE']).copy()
        if 'BLOQUE' in res.columns: res['BLOQUE'] = res['BLOQUE'].astype(str).replace(traductor_bloques)
        st.dataframe(res[[c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res.columns]], hide_index=True, use_container_width=True)

    with tab3:
        esp_sel = st.selectbox("📍 Selecciona el Ámbito:", todos_los_espacios)
        st.divider()
        res_e = df_ocupados[df_ocupados['ESPACIOS'] == esp_sel.upper()].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE']).copy()
        if 'BLOQUE' in res_e.columns: res_e['BLOQUE'] = res_e['BLOQUE'].astype(str).replace(traductor_bloques)
        st.dataframe(res_e[[c for c in ['DIA', 'BLOQUE', 'SUBBLOQUE', 'MATERIA', 'CURSOS', 'DOCENTES'] if c in res_e.columns]], hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")

st.markdown("<style>.footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: grey; padding: 10px; background-color: transparent; z-index: 100; }</style><div class='footer'>by Richard</div>", unsafe_allow_html=True)
