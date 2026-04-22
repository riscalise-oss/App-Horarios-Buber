import streamlit as st
import pandas as pd
import base64
import os
import unicodedata
import re

# --- LIBRERÍAS PARA GOOGLE SHEETS ---
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Buscador de Ámbitos", page_icon="logo.png", layout="wide")

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
    st.warning("⚠️ No se configuraron los secretos de Google.")

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
        except: pass

# --- CSS LIMPIO ---
st.markdown("<style>footer {visibility: hidden !important;} #MainMenu {visibility: hidden !important;}</style>", unsafe_allow_html=True)
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
except:
    st.title("🛡️ Buscador de Ámbitos")

# --- ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [quitar_tildes(c) for c in df_o.columns]
    df_o = df_o.loc[:, ~df_o.columns.duplicated()].copy()
    
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    # --- MOTOR DE FECHAS Y FILTRADO AVANZADO ---
    hoy = pd.Timestamp('today').normalize()
    manana = hoy + pd.Timedelta(days=1)
    limite_2_semanas = manana + pd.Timedelta(days=14)

    df_config['TEMP_FECHA'] = pd.to_datetime(df_config[5], errors='coerce', dayfirst=True)
    df_config = df_config[df_config['TEMP_FECHA'].isna() | (df_config['TEMP_FECHA'] >= hoy)]
    
    avisos = {"hoy": [], "manana": [], "proximas": [], "futuras": []}
    lista_todas_reservas = [] 
    
    # Columna 9 (J) es el Aviso, Columna 10 (K) es el Profe
    for idx, row in df_config.iterrows():
        aviso_ppal = str(row[9]).strip() if len(row) > 9 else ""
        if aviso_ppal and aviso_ppal.upper() not in ["", "NAN", "ESPACIOS BLOQUEADOS"]:
            texto_final = aviso_ppal
            if len(row) > 10 and str(row[10]).upper() not in ["NAN", "NONE", ""]:
                texto_final += f" 👉 *Avisar a: {row[10]}*"
            
            fecha_reserva = row['TEMP_FECHA']
            if pd.isna(fecha_reserva) or fecha_reserva == hoy:
                avisos["hoy"].append(texto_final)
            elif fecha_reserva == manana:
                avisos["manana"].append(texto_final)
            elif fecha_reserva <= limite_2_semanas:
                avisos["proximas"].append(f"🗓️ **[{fecha_reserva.strftime('%d/%m')}]** {texto_final}")
            
            lista_todas_reservas.append({'texto_base': texto_final, 'fecha': fecha_reserva, 'row': row})

    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).map(quitar_tildes)
        orden_dias = {"LUNES": 1, "MARTES": 2, "MIERCOLES": 3, "JUEVES": 4, "VIERNES": 5}
        df_o['ORDEN_DIA'] = df_o['DIA'].map(orden_dias)

    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].astype(str).str.strip().str.upper().str.replace(r'\.0$', '', regex=True)
        df_o['ORDEN_BLOQUE'] = pd.to_numeric(df_o['BLOQUE'], errors='coerce').fillna(99)
        
    espacios = sorted([e for e in df_o['ESPACIOS'].dropna().unique() if e and e != "NAN"])
    return df_o, avisos, espacios, lista_todas_reservas

try:
    df_ocupados, avisos_agrupados, todos_los_espacios, lista_todas_reservas = cargar_datos()

    tab1, tab2, tab3 = st.tabs(["🕰️ Buscar por Horario", "👤 Buscar Docente/Curso", "📍 Buscar por Ámbito"])

    with tab1:
        col_dia, col_bloque = st.columns(2)
        dia_elegido = col_dia.selectbox("📅 Día:", ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"])
        bloque_elegido = col_bloque.selectbox("⏰ Bloque:", ["1", "2", "3", "4", "5", "6"], 
                                              format_func=lambda x: traductor_bloques.get(x))

        st.divider()
        st.header(f"{dia_elegido} - {traductor_bloques.get(bloque_elegido)}")

        # --- LÓGICA DE ESPACIOS LIBRES (MEDIOS BLOQUES) ---
        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == str(bloque_elegido))].copy()
        libres_completos, libres_medio_1, libres_medio_2 = [], [], []
        
        for e in todos_los_espacios:
            df_esp = ocu[ocu['ESPACIOS'] == e]
            if df_esp.empty:
                libres_completos.append(e)
            else:
                subbloques = df_esp['SUBBLOQUE'].astype(str).str.strip().str.upper().tolist()
                if any(s in ["NAN", "", "TODO"] for s in subbloques): continue
                if "1" not in "".join(subbloques): libres_medio_1.append(e)
                if "2" not in "".join(subbloques): libres_medio_2.append(e)

        st.subheader("🟢 Ámbitos Libres")
        if libres_completos: st.success("**Bloque Completo:**\n\n ✅ " + " | ✅ ".join(libres_completos))
        if libres_medio_1: st.info("⏳ **1er Medio Bloque:** ✔️ " + " | ✔️ ".join(libres_medio_1))
        if libres_medio_2: st.info("⏳ **2do Medio Bloque:** ✔️ " + " | ✔️ ".join(libres_medio_2))

        # --- RADAR ULTRA-INTELIGENTE ---
        st.divider()
        st.subheader("📌 Reservas Especiales")
        if avisos_agrupados["hoy"]:
            st.warning("**📍 HOY:**\n\n" + "\n\n".join([f"**•** {a}" for a in avisos_agrupados["hoy"]]))
        
        with st.expander("📅 Ver cronograma de reservas próximas"):
            if avisos_agrupados["proximas"]:
                st.write("\n\n".join(avisos_agrupados["proximas"]))
            else:
                st.write("No hay reservas especiales próximas.")

        # =========================================================================
        # 🚀 FORMULARIO DE RESERVAS (VERSIÓN 500+ LÍNEAS REPARADA) 🚀
        # =========================================================================
        st.divider()
        st.subheader("📝 Registrar Nueva Reserva")
        
        fecha_input = st.date_input("Fecha de la reserva")
        dias_sem = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_nombre = dias_sem[fecha_input.weekday()]
        st.info(f"📅 Día seleccionado: **{dia_nombre}**")

        with st.form("formulario_reserva", clear_on_submit=True):
            c1, c2 = st.columns(2)
            b_in = c1.selectbox("Bloque", ["1", "2", "3", "4", "5", "6"], index=int(bloque_elegido)-1)
            e_in = c1.selectbox("Espacio", todos_los_espacios)
            m_in = c2.text_input("Motivo (Ej: Acto 5to año)")
            p_in = c2.text_input("Avisar al Profesor (Opcional)")
            btn = st.form_submit_button("Guardar Reserva")

        if btn and m_in:
            try:
                doc = cliente.open("2026 ámbitos automatizado 2026")
                hoja = doc.worksheet("Espacios Libres")
                
                # --- VALIDACIÓN ANTIDUPLICADOS ROBUSTA ---
                c_f = hoja.col_values(6) # Fechas
                c_b = hoja.col_values(8) # Bloques
                c_e = hoja.col_values(9) # Espacios
                
                f_str = fecha_input.strftime("%d/%m/%Y")
                if any(c_f[i] == f_str and str(c_b[i]) == str(b_in) and c_e[i].strip().upper() == e_in.strip().upper() for i in range(len(c_f))):
                    st.error(f"❌ El espacio {e_in} ya está reservado para esa fecha y bloque.")
                else:
                    n_fila = len(c_f) + 1
                    hoja.update(f"F{n_fila}:K{n_fila}", [[f_str, dia_nombre, int(b_in), e_in, m_in, p_in]])
                    st.success("✅ ¡Reserva guardada con éxito!")
                    st.balloons()
                    st.cache_data.clear()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # --- PESTAÑA 2: BUSCAR DOCENTE/CURSO ---
    with tab2:
        tipo = st.radio("Buscar por:", ["Docente", "Curso"], horizontal=True)
        col_f = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col_f].dropna().unique() if str(x) != "NAN"])
        sel = st.selectbox(f"Selecciona {tipo}:", lista)
        res = df_ocupados[df_ocupados[col_f] == sel].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE'])
        st.dataframe(res[['DIA', 'BLOQUE', 'SUBBLOQUE', 'ESPACIOS', 'MATERIA', 'CURSOS', 'DOCENTES']], hide_index=True)

    # --- PESTAÑA 3: BUSCAR POR ÁMBITO ---
    with tab3:
        sel_e = st.selectbox("📍 Selecciona el Ámbito:", todos_los_espacios)
        res_e = df_ocupados[df_ocupados['ESPACIOS'] == sel_e].sort_values(['ORDEN_DIA', 'ORDEN_BLOQUE'])
        st.dataframe(res_e[['DIA', 'BLOQUE', 'SUBBLOQUE', 'MATERIA', 'CURSOS', 'DOCENTES']], hide_index=True)

except Exception as e:
    st.error(f"Error técnico: {e}")

st.markdown("<div style='text-align: center; color: grey; padding: 10px;'>by Richard</div>", unsafe_allow_html=True)
