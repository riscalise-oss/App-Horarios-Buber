import streamlit as st
import pandas as pd

# 1. Título y descripción de tu app
st.title("🏫 Buscador de Horarios Escolares")
st.write("Bienvenido. Aquí podrás consultar la disponibilidad de espacios y docentes.")

# 2. Tu enlace secreto de Google Sheets (¡Reemplaza el texto entre comillas!)
LINK_CSV = "https://docs.google.com/spreadsheets/d/1SjAgVIr08IT0B0qBGo3boRaT6ObKQGPFfrzE-kmZ394/edit?gid=0#gid=0"

# 3. Función para leer los datos (con memoria para que sea rápido)
@st.cache_data
def cargar_datos():
    # Leemos el archivo CSV desde el enlace
    datos = pd.read_csv(LINK_CSV)
    return datos

# 4. Ejecutar la función y guardar los datos en una variable
df = cargar_datos()

# 5. Mostrar la tabla en pantalla para probar que funciona
st.write("### Vista previa de los datos:")
st.dataframe(df)
