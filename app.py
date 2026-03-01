import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")
st.title("🏫 Buscador de Ámbitos")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=447717872&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_datos():
    # 1. LEER ASIGNACIONES REGULARES
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    # 2. LEER TU HOJA DE RESERVAS
    df_config = pd.read_csv(LINK_RESERVAS, header=None, on_bad_lines='skip', engine='python')
    
    avisos_col_d = []
    
    # ESTRATEGIA A: Buscar la columna exacta por tu título amarillo
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
        # ESTRATEGIA B: Si no encuentra el título, buscamos los ⚠️ en TODA la hoja
        for col in range(len(df_config.columns)):
            for val in df_config.iloc
