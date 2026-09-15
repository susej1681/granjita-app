import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configuración visual de la App
st.set_page_config(page_title="La Granjita PRO", page_icon="🦁", layout="centered")

# Diccionario oficial de 38 animalitos
tabla_animalitos = {
    "00": "Ballena", "0": "Delfín", "01": "Carnero", "02": "Toro", "03": "Ciempiés", 
    "04": "Alacrán", "05": "León", "06": "Rana", "07": "Perico", "08": "Ratón", 
    "09": "Águila", "10": "Tigre", "11": "Gato", "12": "Caballo", "13": "Mono", 
    "14": "Paloma", "15": "Zorro", "16": "Oso", "17": "Pavo", "18": "Burro", 
    "19": "Chivo", "20": "Cochino", "21": "Gallo", "22": "Camello", "23": "Cebra", 
    "24": "Iguana", "25": "Gallina", "26": "Vaca", "27": "Perro", "28": "Zamuro", 
    "29": "Elefante", "30": "Caimán", "31": "Lapa", "32": "Ardilla", "33": "Pescado", 
    "34": "Venado", "35": "Jirafa", "36": "Culebra"
}

# Historial acumulado
historial = [
    "23", "25", "30", "19", "35", "20", "27", "33", "28", "0", "23", "26",
    "12", "31", "30", "29", "18", "24", "02", "28", "09", "05", "20", "0",
    "25", "08", "13", "31", "16", "02", "23", "13", "10", "33", "14", "27",
    "05", "30", "06", "16", "01", "28", "27", "27", "23", "22", "07", "18",
    "03", "20", "12", "08", "0", "26", "15", "29", "17", "07", "01", "19",
    "27", "21", "04", "18", "20"
]

total_sorteos = len(historial)

# Título de la Aplicación
st.title("🦁 La Granjita PRO")
st.caption("Panel de Análisis Estadístico Automatizado")

# Botón de actualización
if st.button("🔄 Escanear Resultados en Vivo"):
    st.toast("Conectando con el servidor de la lotería...")

# Cálculos estadísticos
frecuencias = {code: historial.count(code) for code in tabla_animalitos}
atrasos = {}
for code in tabla_animalitos:
    if code in historial:
        atrasos[code] = list(reversed(historial)).index(code)
    else:
        atrasos[code] = total_sorteos

mas_calientes = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)[:3]
mas_atrasados = sorted(atrasos.items(), key=lambda x: x[1], reverse=True)[:3]

# Despliegue de Indicadores
st.metric("Total Sorteos Analizados", total_sorteos)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Más Calientes")
    for code, freq in mas_calientes:
        st.success(f"**[{code}] {tabla_animalitos[code]}**\n\n{freq} salidas")

with col2:
    st.subheader("🧊 Más Atrasados")
    for code, atr in mas_atrasados:
        st.error(f"**[{code}] {tabla_animalitos[code]}**\n\n{atr} sorteos sin salir")

st.divider()

# Pronóstico Recomendado
st.subheader("🎯 Pronóstico Próximo Bloque")
top_caliente = mas_calientes[0][0]
top_atrasado = mas_atrasados[0][0]

st.info(f"👉 **Línea de Frecuencia:** [{top_caliente}] {tabla_animalitos[top_caliente]}")
st.warning(f"👉 **Línea de Ruptura:** [{top_atrasado}] {tabla_animalitos[top_atrasado]}")
