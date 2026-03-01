import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Espacios", layout="wide")
st.title("🏫 Buscador Rápido para Asistentes")

# --- 1. TUS ENLACES ---
LINK_OCUPADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=727803976&single=true&output=csv"
LINK_RESERVAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ0A2kjdA80XSzjxLZBlutVdgmY5wl78w2GqjYA9HMhK8SJ-WbCS_ixqrYLubXRuG6-KbKm3K9C7yHW/pub?gid=0&single=true&output=csv"

@st.cache_data
def cargar_datos():
    # 1. LEER ASIGNACIONES REGULARES
    df_o = pd.read_csv(LINK_OCUPADOS)
    df_o.columns = [str(c).upper().strip().replace('Í', 'I') for c in df_o.columns]
    
    # 2. LEER TU COLUMNA 'D' (Reservas Especiales)
    # Leemos sin encabezados para asegurar que capturamos la columna exacta
    df_config = pd.read_csv(LINK_RESERVAS, header=None)
    # La Columna D es la número 3 (A=0, B=1, C=2, D=3)
    columna_d_bruta = df_config.iloc[:, 3].dropna().astype(str).tolist()
    # Limpiamos celdas vacías o el título de la columna para que quede prolijo
    avisos_col_d = [a.strip() for a in columna_d_bruta if a.strip() != "" and a.strip().upper() not in ["RESERVAS", "RESERVA", "RESERVAS ESPECIALES"]]

    def limpiar_bloque(val):
        val_str = str(val).strip().upper()
        if val_str.endswith('.0'):
            return val_str[:-2]
        return val_str

    # LIMPIEZA DE DATOS REGULARES
    if 'DIA' in df_o.columns:
        df_o['DIA'] = df_o['DIA'].astype(str).str.strip().str.upper().str.replace('Í', 'I')
    if 'BLOQUE' in df_o.columns:
        df_o['BLOQUE'] = df_o['BLOQUE'].apply(limpiar_bloque)
    if 'ESPACIOS' in df_o.columns:
        df_o['ESPACIOS'] = df_o['ESPACIOS'].astype(str).str.strip().str.upper()

    # LISTA DE ESPACIOS TOTALES
    espacios = df_o['ESPACIOS'].dropna().unique().tolist()
    espacios_totales = sorted([e for e in espacios if e != "NAN" and e != ""])
    
    return df_o, avisos_col_d, espacios_totales

try:
    df_ocupados, avisos_col_d, todos_los_espacios = cargar_datos()

    # --- MENÚ LATERAL ---
    st.sidebar.header("⚙️ Opciones")
    modo = st.sidebar.radio("Selecciona modo:", ["🕰️ Buscar por Horario", "🧑‍🏫 Buscar Docente/Curso"])
    st.sidebar.divider()

    # --- MODO 1: HORARIO ---
    if modo == "🕰️ Buscar por Horario":
        dias = [d for d in df_ocupados['DIA'].dropna().unique() if d != "NAN"]
        dia_elegido = st.sidebar.selectbox("📅 Día:", dias)
        
        bloques = [b for b in df_ocupados[df_ocupados['DIA'] == dia_elegido]['BLOQUE'].dropna().unique() if b != "NAN"]
        bloque_elegido = st.sidebar.selectbox("⏰ Bloque:", bloques)

        st.header(f"Resultados: {dia_elegido} - Bloque {bloque_elegido}")

        # --- AVISOS DE LA COLUMNA D ---
        st.subheader("📌 Reservas Especiales (Avisos)")
        if avisos_col_d:
            for aviso in avisos_col_d:
                st.info(f"📝 {aviso}")
        else:
            st.write("No hay reservas especiales anotadas.")

        # --- LÓGICA DE ESPACIOS LIBRES (Solo resta los regulares) ---
        ocu = df_ocupados[(df_ocupados['DIA'] == dia_elegido) & (df_ocupados['BLOQUE'] == bloque_elegido)]
        lista_ocupados = ocu['ESPACIOS'].dropna().tolist() if 'ESPACIOS' in ocu.columns else []
        espacios_libres = [espacio for espacio in todos_los_espacios if espacio not in lista_ocupados]

        st.subheader("🟢 Espacios sin clases regulares")
        if espacios_libres:
            st.success(" ✅ " + " | ✅ ".join(sorted(espacios_libres)))
        else:
            st.warning("No hay ningún espacio libre en este horario.")

        # --- CLASES REGULARES ---
        st.subheader("🔴 Clases Regulares")
        if not ocu.empty:
            cols_mostrar = ['ESPACIOS', 'CURSOS', 'DOCENTES', 'MATERIA']
            cols_finales = [c for c in cols_mostrar if c in ocu.columns]
            st.dataframe(ocu[cols_finales], hide_index=True, use_container_width=True)
        else:
            st.write("No hay clases regulares registradas.")

    # --- MODO 2: BÚSQUEDA ---
    else:
        tipo = st.sidebar.radio("Buscar por:", ["Docente", "Curso"])
        col = 'DOCENTES' if tipo == "Docente" else 'CURSOS'
        lista = sorted([x for x in df_ocupados[col].dropna().unique() if str(x).upper() != "NAN"])
        sel = st.sidebar.selectbox(f"Selecciona {tipo}:", lista)
        
        st.header(f"Agenda de: {sel}")
        res_busqueda = df_ocupados[df_ocupados[col] == sel]
        st.dataframe(res_busqueda, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
