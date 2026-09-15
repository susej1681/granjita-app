import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="La Granjita Pro - Analizador Inteligente",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para un look moderno y limpio
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .sweet-zone { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50; }
    .alert-box { background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DICCIONARIO DE ANIMALITOS DE LA GRANJITA
# ==========================================
ANIMALES_MAP = {
    "00": "Ballena", "0": "Delfín", "01": "Carnero", "02": "Toro", "03": "Ciempiés", 
    "04": "Alacrán", "05": "León", "06": "Rana", "07": "Perico", "08": "Ratón", 
    "09": "Águila", "10": "Tigre", "11": "Gato", "12": "Caballo", "13": "Mono", 
    "14": "Paloma", "15": "Zorro", "16": "Oso", "17": "Pavo", "18": "Burro", 
    "19": "Chivo", "20": "Cochino", "21": "Gallo", "22": "Camello", "23": "Cebra", 
    "24": "Iguana", "25": "Gallina", "26": "Vaca", "27": "Perro", "28": "Zamuro", 
    "29": "Elefante", "30": "Caimán", "31": "Lapa", "32": "Ardilla", "33": "Pescado", 
    "34": "Venado", "35": "Jirafa", "36": "Culebra"
}

# ==========================================
# BASE DE DATOS Y VENTANA DESLIZANTE DE 48 SORTEOS
# ==========================================
@st.cache_data
def cargar_base_datos():
    datos_crudos = [
        # 10/09/2026
        ("10/09/2026", "08:00 AM", "23"), ("10/09/2026", "09:00 AM", "25"), ("10/09/2026", "10:00 AM", "30"),
        ("10/09/2026", "11:00 AM", "19"), ("10/09/2026", "12:00 PM", "35"), ("10/09/2026", "01:00 PM", "20"),
        ("10/09/2026", "02:00 PM", "27"), ("10/09/2026", "03:00 PM", "33"), ("10/09/2026", "04:00 PM", "28"),
        ("10/09/2026", "05:00 PM", "0"),  ("10/09/2026", "06:00 PM", "23"), ("10/09/2026", "07:00 PM", "26"),
        # 11/09/2026
        ("11/09/2026", "08:00 AM", "12"), ("11/09/2026", "09:00 AM", "31"), ("11/09/2026", "10:00 AM", "30"),
        ("11/09/2026", "11:00 AM", "29"), ("11/09/2026", "12:00 PM", "18"), ("11/09/2026", "01:00 PM", "24"),
        ("11/09/2026", "02:00 PM", "02"), ("11/09/2026", "03:00 PM", "28"), ("11/09/2026", "04:00 PM", "09"),
        ("11/09/2026", "05:00 PM", "05"), ("11/09/2026", "06:00 PM", "20"), ("11/09/2026", "07:00 PM", "0"),
        # 12/09/2026
        ("12/09/2026", "08:00 AM", "25"), ("12/09/2026", "09:00 AM", "08"), ("12/09/2026", "10:00 AM", "13"),
        ("12/09/2026", "11:00 AM", "31"), ("12/09/2026", "12:00 PM", "16"), ("12/09/2026", "01:00 PM", "02"),
        ("12/09/2026", "02:00 PM", "23"), ("12/09/2026", "03:00 PM", "13"), ("12/09/2026", "04:00 PM", "10"),
        ("12/09/2026", "05:00 PM", "33"), ("12/09/2026", "06:00 PM", "14"), ("12/09/2026", "07:00 PM", "27"),
        # 13/09/2026
        ("13/09/2026", "08:00 AM", "05"), ("13/09/2026", "09:00 AM", "30"), ("13/09/2026", "10:00 AM", "06"),
        ("13/09/2026", "11:00 AM", "16"), ("13/09/2026", "12:00 PM", "01"), ("13/09/2026", "01:00 PM", "28"),
        ("13/09/2026", "02:00 PM", "27"), ("13/09/2026", "03:00 PM", "27"), ("13/09/2026", "04:00 PM", "23"),
        ("13/09/2026", "05:00 PM", "22"), ("13/09/2026", "06:00 PM", "07"), ("13/09/2026", "07:00 PM", "18"),
        # 14/09/2026
        ("14/09/2026", "08:00 AM", "03"), ("14/09/2026", "09:00 AM", "20"), ("14/09/2026", "10:00 AM", "12"),
        ("14/09/2026", "11:00 AM", "08"), ("14/09/2026", "12:00 PM", "0"),  ("14/09/2026", "01:00 PM", "26"),
        ("14/09/2026", "02:00 PM", "15"), ("14/09/2026", "03:00 PM", "29"), ("14/09/2026", "04:00 PM", "17"),
        ("14/09/2026", "05:00 PM", "07"), ("14/09/2026", "06:00 PM", "01"), ("14/09/2026", "07:00 PM", "19"),
        # 15/09/2026
        ("15/09/2026", "08:00 AM", "27"), ("15/09/2026", "09:00 AM", "21"), ("15/09/2026", "10:00 AM", "04"),
        ("15/09/2026", "11:00 AM", "18"), ("15/09/2026", "12:00 PM", "20")
    ]
    
    lista = []
    for fecha, hora, num in datos_crudos:
        num_fmt = num.zfill(2) if len(num) == 1 and num != "0" else ("0" if num == "0" else num)
        lista.append({
            "Fecha": fecha,
            "Hora": hora,
            "Numero": num_fmt,
            "Animal": ANIMALES_MAP.get(num_fmt, "Desconocido")
        })
    df = pd.DataFrame(lista)
    # Ventana deslizante estricta de los últimos 48 sorteos
    return df.tail(48).reset_index(drop=True)

# ==========================================
# MOTOR DE ANÁLISIS ESTADÍSTICO
# ==========================================
def ejecutar_motor_analisis(df):
    total_sorteos = len(df)
    
    # 1. Frecuencias y Atrasos Reales
    stats = {}
    for num, nombre in ANIMALES_MAP.items():
        apariciones = df[df['Numero'] == num].index.tolist()
        freq = len(apariciones)
        
        if apariciones:
            atraso = total_sorteos - 1 - apariciones[-1]
        else:
            atraso = total_sorteos
            
        stats[num] = {
            "Animal": f"{num} - {nombre}",
            "Frecuencia": freq,
            "Atraso": atraso
        }
        
    df_stats = pd.DataFrame.from_dict(stats, orient='index')
    
    # 2. Patrón Jala-Jala (Matriz de Transición)
    transiciones = {num: {n: 0 for n in ANIMALES_MAP.keys()} for num in ANIMALES_MAP.keys()}
    
    numeros_sucesion = df['Numero'].tolist()
    for i in range(len(numeros_sucesion) - 1):
        actual = numeros_sucesion[i]
        siguiente = numeros_sucesion[i+1]
        transiciones[actual][siguiente] += 1
        
    ultimo_animal = numeros_sucesion[-1] if numeros_sucesion else "20"
    
    candidatos_jala = transiciones.get(ultimo_animal, {})
    df_stats['Jala_Score'] = df_stats.index.map(lambda x: candidatos_jala.get(x, 0))
    
    # 3. Cálculo de la "Zona Dulce"
    max_atraso = max(1, df_stats['Atraso'].max())
    max_jala = max(1, df_stats['Jala_Score'].max())
    
    df_stats['Score_Zona_Dulce'] = (
        (df_stats['Atraso'] / max_atraso) * 0.4 + 
        (df_stats['Jala_Score'] / max_jala) * 0.6
    ) * 100
    
    df_stats = df_stats.sort_values(by='Score_Zona_Dulce', ascending=False)
    return df_stats, ultimo_animal

# ==========================================
# INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
def main():
    st.title("🐾 La Granjita Pro - Analizador y Predictor")
    st.markdown("Sistema analítico automatizado exclusivo para **La Granjita**, operando bajo una ventana deslizante estricta de **48 sorteos**.")

    # Cargar historial y ejecutar motor analítico
    df_historial = cargar_base_datos()
    df_analisis, ultimo_salido = ejecutar_motor_analisis(df_historial)

    # Mostrar último resultado detectado
    st.markdown("---")
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.metric(label="Último Animal Saliendo", value=f"{ultimo_salido} - {ANIMALES_MAP.get(ultimo_salido, '')}")
    with col_u2:
        st.markdown(f"""
        <div class="alert-box">
        <b>💡 Análisis Jala-Jala Activo:</b> El último animal registrado es el <b>{ultimo_salido} ({ANIMALES_MAP.get(ultimo_salido, '')})</b>. 
        El motor ha evaluado las probabilidades de transición directa para predecir los siguientes arrastres óptimos.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN 1: TOP 3 RECOMENDADOS (ZONA DULCE)
    st.subheader("🎯 Top 3 Animalitos en 'Zona Dulce'")
    top_3 = df_analisis.head(3)
    
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    
    for i, (idx, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.markdown(f"""
            <div class="sweet-zone">
                <h3>#{i+1} - {row['Animal']}</h3>
                <p><b>Puntuación Zona Dulce:</b> {row['Score_Zona_Dulce']:.1f}%</p>
                <p>📊 Frecuencia (48h): {row['Frecuencia']} | ⏳ Atraso: {row['Atraso']} sorteos</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN 2: TRIPLETAS FUERTES Y JUGADAS INDIVIDUALES (SIN QUINIELA)
    col_A, col_B = st.columns(2)

    with col_A:
        st.subheader("🔥 Tripletas Fuertes Recomendadas")
        st.markdown("Combinaciones de alta probabilidad basadas en convergencia de atrasos y patrones jala-jala:")
        
        top_nums = df_analisis.index.tolist()
        if len(top_nums) >= 9:
            tripletas = [
                f"{top_nums[0]} ({ANIMALES_MAP[top_nums[0]]}) - {top_nums[3]} ({ANIMALES_MAP[top_nums[3]]}) - {top_nums[6]} ({ANIMALES_MAP[top_nums[6]]})",
                f"{top_nums[1]} ({ANIMALES_MAP[top_nums[1]]}) - {top_nums[4]} ({ANIMALES_MAP[top_nums[4]]}) - {top_nums[7]} ({ANIMALES_MAP[top_nums[7]]})",
                f"{top_nums[2]} ({ANIMALES_MAP[top_nums[2]]}) - {top_nums[5]} ({ANIMALES_MAP[top_nums[5]]}) - {top_nums[8]} ({ANIMALES_MAP[top_nums[8]]})"
            ]
            for t in tripletas:
                st.success(f"✨ **Tripleta:** {t}")
        else:
            st.warning("Datos insuficientes para tripletas.")

    with col_B:
        st.subheader("🎲 Jugadas Individuales Directas")
        st.markdown("Selección optimizada para jugadas fijas y directas:")
        
        df_individuales = df_analisis[['Animal', 'Frecuencia', 'Atraso', 'Score_Zona_Dulce']].head(5)
        df_individuales.columns = ['Animalito', 'Freq.', 'Atraso', 'Score %']
        st.dataframe(df_individuales, use_container_width=True)

    st.markdown("---")

    # SECCIÓN 3: HISTORIAL DESLIZANTE DE LOS ÚLTIMOS 48 SORTEOS
    st.subheader("📜 Historial Deslizante (Últimos 48 Sorteos)")
    st.dataframe(df_historial, use_container_width=True)

if __name__ == '__main__':
    main()
