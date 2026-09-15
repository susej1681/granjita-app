import datetime
from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="La Granjita - Análisis Inteligente", layout="centered"
)

# ==========================================
# BASE DE DATOS HISTÓRICA - LA GRANJITA
# ==========================================
HISTORICAL_DATA = {
    "13/09/2026": {
        "08:00 AM": "05 León",
        "09:00 AM": "30 Caimán",
        "10:00 AM": "06 Rana",
        "11:00 AM": "16 Oso",
        "12:00 PM": "01 Carnero",
        "01:00 PM": "28 Zamuro",
        "02:00 PM": "27 Perro",
        "03:00 PM": "27 Perro",
        "04:00 PM": "23 Cebra",
        "05:00 PM": "22 Camello",
        "06:00 PM": "07 Perico",
        "07:00 PM": "18 Burro",
    },
    "14/09/2026": {
        "08:00 AM": "03 Ciempiés",
        "09:00 AM": "20 Cochino",
        "10:00 AM": "12 Caballo",
        "11:00 AM": "08 Ratón",
        "12:00 PM": "0 Delfín",
        "01:00 PM": "26 Vaca",
        "02:00 PM": "15 Zorro",
        "03:00 PM": "29 Elefante",
        "04:00 PM": "17 Pavo",
        "05:00 PM": "07 Perico",
        "06:00 PM": "01 Carnero",
        "07:00 PM": "19 Chivo",
    },
    "15/09/2026": {
        "08:00 AM": "27 Perro",
        "09:00 AM": "21 Gallo",
        "10:00 AM": "04 Alacrán",
        "11:00 AM": "18 Burro",
        "12:00 PM": "20 Cochino",
        "01:00 PM": "33 Pescado",
        "02:00 PM": "11 Gato",
        "03:00 PM": "00 Ballena",
    },
}

TABLA_ANIMALES = {
    "00": "Ballena",
    "0": "Delfín",
    "01": "Carnero",
    "02": "Toro",
    "03": "Ciempiés",
    "04": "Alacrán",
    "05": "León",
    "06": "Rana",
    "07": "Perico",
    "08": "Ratón",
    "09": "Águila",
    "10": "Tigre",
    "11": "Gato",
    "12": "Caballo",
    "13": "Mono",
    "14": "Paloma",
    "15": "Zorro",
    "16": "Oso",
    "17": "Pavo",
    "18": "Burro",
    "19": "Chivo",
    "20": "Cochino",
    "21": "Gallo",
    "22": "Camello",
    "23": "Cebra",
    "24": "Iguana",
    "25": "Gallina",
    "26": "Vaca",
    "27": "Perro",
    "28": "Zamuro",
    "29": "Elefante",
    "30": "Caimán",
    "31": "Lapa",
    "32": "Ardilla",
    "33": "Pescado",
    "34": "Venado",
    "35": "Jirafa",
    "36": "Culebra",
}


class MotorGranjita:

  def __init__(self, database):
    self.db = database
    self.secuencia_sorteos = self._aplanar_datos()

  def _aplanar_datos(self):
    lista = []
    for fecha in sorted(
        self.db.keys(),
        key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"),
    ):
      for hora in sorted(self.db[fecha].keys()):
        lista.append((fecha, hora, self.db[fecha][hora]))
    return lista

  def calcular_estadisticas(self):
    frecuencias = {num: 0 for num in TABLA_ANIMALES.keys()}
    ultimo_idx = {num: -999 for num in TABLA_ANIMALES.keys()}
    total_sorteos = len(self.secuencia_sorteos)

    for idx, (fecha, hora, animal_str) in enumerate(self.secuencia_sorteos):
      num = animal_str.split(" ")[0]
      if num in frecuencias:
        frecuencias[num] += 1
        ultimo_idx[num] = idx

    atrasos = {}
    for num in TABLA_ANIMALES.keys():
      if ultimo_idx[num] == -999:
        # Corrección: si no salió en la muestra reciente, se le asigna un atraso base realista, no artificialmente gigante
        atrasos[num] = int(total_sorteos * 0.5)
      else:
        atrasos[num] = (total_sorteos - 1) - ultimo_idx[num]

    return frecuencias, atrasos

  def calcular_jala_jala(self):
    transiciones = {num: {} for num in TABLA_ANIMALES.keys()}
    for i in range(len(self.secuencia_sorteos) - 1):
      _, _, actual_str = self.secuencia_sorteos[i]
      _, _, siguiente_str = self.secuencia_sorteos[i + 1]

      curr_num = actual_str.split(" ")[0]
      next_num = siguiente_str.split(" ")[0]

      if next_num not in transiciones[curr_num]:
        transiciones[curr_num][next_num] = 0
      transiciones[curr_num][next_num] += 1

    if self.secuencia_sorteos:
      _, _, ultimo_salido_str = self.secuencia_sorteos[-1]
      ultimo_num = ultimo_salido_str.split(" ")[0]
      jalados = transiciones.get(ultimo_num, {})
      ranking_jalados = sorted(jalados.items(), key=lambda x: x[1], reverse=True)
      return ultimo_num, ranking_jalados
    return None, []

  def generar_recomendaciones(self):
    frecuencias, atrasos = self.calcular_estadisticas()
    ultimo_num, ranking_jalados = self.calcular_jala_jala()

    puntajes = {}
    for num in TABLA_ANIMALES.keys():
      # Fórmula equilibrada: Frecuencia real + Atraso moderado + Impulso de Jala-Jala
      score = (frecuencias[num] * 3.0) + (atrasos[num] * 0.5)
      puntajes[num] = score

    for num, freq_jala in ranking_jalados:
      if num in puntajes:
        puntajes[num] += freq_jala * 8.0  # El jala-jala real manda fuerte

    ranking = sorted(puntajes.items(), key=lambda x: x[1], reverse=True)
    return ranking, frecuencias, atrasos, ultimo_num


st.title("🐔 La Granjita - Análisis Inteligente")
st.markdown("---")

engine = MotorGranjita(HISTORICAL_DATA)
ranking, frecuencias, atrasos, ultimo_num = engine.generar_recomendaciones()

st.subheader("📊 Estado Actual del Motor")
col1, col2 = st.columns(2)
with col1:
  st.metric("Total Sorteos Analizados", len(engine.secuencia_sorteos))
with col2:
  if ultimo_num:
    st.metric(
        "Último Animal", f"[{ultimo_num}] {TABLA_ANIMALES.get(ultimo_num, '')}"
    )

st.markdown("---")
st.subheader("🔥 Top 3 Animalitos en Zona Dulce")
for i in range(min(3, len(ranking))):
  num, score = ranking[i]
  nombre = TABLA_ANIMALES[num]
  st.write(
      f"**{i+1}. [{num}] {nombre}** — Score: `{score:.1f}` | Salidas:"
      f" `{frecuencias[num]}` | Atraso: `{atrasos[num]}` sorteos"
  )

st.markdown("---")
st.subheader("🎯 Sugerencia de Tripletas y Quiniela")
t1 = (
    f"[{ranking[0][0]}]"
    f" {TABLA_ANIMALES.get(ranking[0][0], 'Desconocido')}"
)
t2 = (
    f"[{ranking[1][0]}]"
    f" {TABLA_ANIMALES.get(ranking[1][0], 'Desconocido')}"
)
t3 = (
    f"[{ranking[2][0]}]"
    f" {TABLA_ANIMALES.get(ranking[2][0], 'Desconocido')}"
)
# Buscamos un cuarto por si acaso para la tripleta combinada
t4 = (
    f"[{ranking[3][0]}]"
    f" {TABLA_ANIMALES.get(ranking[3][0], 'Desconocido')}"
    if len(ranking) > 3
    else t3
)

st.success(f"• **Quiniela recomendada:** {t1} - {t2} - {t3}")
st.info(f"• **Tripleta fuerte de la tarde:** {t1} con {t2} y {t4}")
