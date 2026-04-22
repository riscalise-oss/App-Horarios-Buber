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
    st.warning("⚠️ Todavía no se configuraron los secretos de Google.")

# ==============================================================================
# --- FUNCIONES AUXILIARES ---
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
            st.markdown(f'<style>.stApp {{background-image: url("data:image/png;base64,{img_base64}"); background-size: cover; background-attachment: fixed;}}</style>', unsafe_allow_html=True)
        except: pass

# --- CSS Y FONDO ---
st.markdown("<style>footer {visibility: hidden !important;} #MainMenu {visibility: hidden !important;}</style>", unsafe_allow_html=True)
aplicar_fondo_institucional("fondo.png")

traductor_bloques = {
    "1": "1. 7:40 a 9:00", "2": "2. 9:10 a 10:30", "3": "3. 10:45 a 12:05",
    "4": "4. 12:15 a 13:35", "5": "5. 13:45 a 15:00", "6": "6. 15:10 a 16:30"
}

# --- CARGA DE DATOS ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [quitar_tildes(c) for c in df_o.columns]
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    hoy = pd.Timestamp('today').normalize()
    manana = hoy + pd.Timedelta(days=1)
    
    # Motor de fechas simplificado para evitar errores de duplicados
    df_config['TEMP_FECHA'] = pd.to_datetime(df_config[5], errors='coerce', dayfirst=True)
    df_config = df_config[df_config['TEMP_FECHA'].isna() | (df_config['TEMP_FECHA'] >= hoy)]
    
    avisos = {"hoy": [], "manana": [], "proximas": [], "futuras": []}
    lista_todas_reservas = []
    
    # Procesamiento de avisos (Columna J para avisos principales)
    for idx, row in df_config.iterrows():
        aviso = str(row[9]).strip() if len(row) > 9 else ""
        if aviso and aviso.upper() not in ["", "NAN", "ESPACIOS BLOQUEADOS"]:
            fecha_res = row['TEMP_FECHA']
            texto = f"{aviso} (Bloque {row[7]})" if len(row) > 7 else aviso
            lista_todas_reservas.append({'texto_base': texto, 'fecha': fecha_res, 'row': row})
            
            if pd.isna(fecha_res) or fecha_res == hoy: avisos["hoy"].append(texto)
            elif fecha_res == manana: avisos["manana"].append(texto)
            else: avisos["proximas"].append(f"🗓️ **[{fecha_res.strftime('%d/%m')}]** {texto}")

    espacios = sorted([e for e in df_o['ESPACIOS'].dropna().unique() if e])
    return df_o, avisos, espacios, lista_todas_reservas

try:
    df_ocupados, avisos_agrupados, todos_los_espacios, lista_todas_reservas = cargar_datos()
    tab1, tab2, tab3 = st.tabs(["🕰️ Horario", "👤 Docente/Curso", "📍 Ámbito"])

    with tab1:
        col_dia, col_bloque = st.columns(2)
        dia_elegido = col_dia.selectbox("📅 Día:", ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"])
        bloque_elegido = col_bloque.selectbox("⏰ Bloque:", ["1", "2", "3", "4", "5", "6"], format_func=lambda x: traductor_bloques.get(x))

        # Lógica de visualización simplificada...
        st.header(f"{dia_elegido} - Bloque {bloque_elegido}")
        # (Aquí va la lógica de espacios libres que ya tenías)

        # =========================================================================
        # 🚀 FORMULARIO DE RESERVAS (ESTRUCTURA ROBUSTA) 🚀
        # =========================================================================
        st.divider()
        st.subheader("📝 Registrar Nueva Reserva")
        
        fecha_input = st.date_input("Fecha de la reserva")
        dias_sem = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_nombre = dias_sem[fecha_input.weekday()]
        st.info(f"Seleccionado: **{dia_nombre}**")

        with st.form("form_reserva", clear_on_submit=True):
            c1, c2 = st.columns(2)
            bloque_ins = c1.selectbox("Bloque", ["1", "2", "3", "4", "5", "6"], index=int(bloque_elegido)-1)
            espacio_ins = c1.selectbox("Espacio", todos_los_espacios)
            motivo_ins = c2.text_input("Motivo")
            profe_ins = c2.text_input("Avisar al Profesor (Opcional)")
            enviar = st.form_submit_button("Guardar Reserva")

        if enviar and motivo_ins:
            try:
                doc = cliente.open("2026 ámbitos automatizado 2026")
                hoja = doc.worksheet("Espacios Libres")
                
                # Leemos solo columnas específicas para evitar el error de headers duplicados
                todas_las_fechas = hoja.col_values(6) # Col F
                todos_los_bloques = hoja.col_values(8) # Col H
                todos_los_espacios_res = hoja.col_values(9) # Col I
                
                fecha_buscada = fecha_input.strftime("%d/%m/%Y")
                
                # Validación de duplicados
                duplicado = False
                for i in range(len(todas_las_fechas)):
                    if (todas_las_fechas[i] == fecha_buscada and 
                        str(todos_los_bloques[i]) == str(bloque_ins) and 
                        str(todos_los_espacios_res[i]).strip().upper() == str(espacio_ins).strip().upper()):
                        duplicado = True
                        break
                
                if duplicado:
                    st.error(f"❌ Ya existe una reserva para {espacio_ins} en el bloque {bloque_ins} el día {fecha_buscada}.")
                else:
                    # Escribimos en la siguiente fila vacía basada en la columna F
                    proxima_fila = len(todas_las_fechas) + 1
                    hoja.update(f"F{proxima_fila}:K{proxima_fila}", 
                               [[fecha_buscada, dia_nombre, int(bloque_ins), espacio_ins, motivo_ins, profe_ins]])
                    st.success("✅ Reserva guardada correctamente.")
                    st.balloons()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # Resto de pestañas (Búsqueda docente/ámbito)...
    # ... (Se mantiene igual al código anterior)

except Exception as e:
    st.error(f"Error: {e}")
