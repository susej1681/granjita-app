import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="La Granjita Pro - Control Total",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# ESTADO INICIAL: 4 DÍAS DE HISTORIAL OFICIAL EXTRAÍDO DE TUS CAPTURAS
# ==========================================
if 'df_sorteos' not in st.session_state:
    horas_sorteos = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
                     "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", 
                     "06:00 PM", "07:00 PM"]
    
    datos_iniciales = []
    
    # 1. Día 12/09/2026 (Extraído de captura)
    res_12 = ["25", "08", "13", "31", "16", "02", "23", "13", "10", "33", "14", "27"]
    for h, num in zip(horas_sorteos, res_12):
        datos_iniciales.append({"Fecha": "12/09/2026", "Hora": h, "Numero": num, "Animal": ANIMALES_MAP.get(num, "")})
        
    # 2. Día 13/09/2026 (Extraído de captura)
    res_13 = ["05", "30", "06", "16", "01", "28", "27", "27", "23", "22", "07", "18"]
    for h, num in zip(horas_sorteos, res_13):
        datos_iniciales.append({"Fecha": "13/09/2026", "Hora": h, "Numero": num, "Animal": ANIMALES_MAP.get(num, "")})
        
    # 3. Día 14/09/2026 (Extraído de captura)
    res_14 = ["03", "20", "12", "08", "0", "26", "15", "29", "17", "07", "01", "19"]
    for h, num in zip(horas_sorteos, res_14):
        datos_iniciales.append({"Fecha": "14/09/2026", "Hora": h, "Numero": num, "Animal": ANIMALES_MAP.get(num, "")})
        
    # 4. Día 15/09/2026 (Hoy - Hasta las 5 PM con Elefante 29 y vacías las que faltan)
    res_15 = ["27", "21", "04", "18", "20", "13", "21", "01", "25", "29", "", ""]
    for h, num in zip(horas_sorteos, res_15):
        animal = ANIMALES_MAP.get(num, "") if num in ANIMALES_MAP else ""
        datos_iniciales.append({"Fecha": "15/09/2026", "Hora": h, "Numero": num, "Animal": animal})

    st.session_state['df_sorteos'] = pd.DataFrame(datos_iniciales)

# ==========================================
# MOTOR DE ANÁLISIS ESTADÍSTICO
# ==========================================
def ejecutar_motor_analisis(df_data):
    df_valido = df_data[df_data['Numero'].astype(str).isin(ANIMALES_MAP.keys())].copy()
    total_sorteos = len(df_valido)
    
    if total_sorteos == 0:
        return pd.DataFrame(), "29"
    
    stats = {}
    for num, nombre in ANIMALES_MAP.items():
        apariciones = df_valido[df_valido['Numero'] == num].index.tolist()
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
    
    # Patrón Jala-Jala
    transiciones = {num: {n: 0 for n in ANIMALES_MAP.keys()} for num in ANIMALES_MAP.keys()}
    numeros_sucesion = df_valido['Numero'].tolist()
    for i in range(len(numeros_sucesion) - 1):
        actual = numeros_sucesion[i]
        siguiente = numeros_sucesion[i+1]
        transiciones[actual][siguiente] += 1
        
    ultimo_animal = numeros_sucesion[-1] if numeros_sucesion else "29"
    candidatos_jala = transiciones.get(ultimo_animal, {})
    df_stats['Jala_Score'] = df_stats.index.map(lambda x: candidatos_jala.get(x, 0))
    
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
    st.title("🐾 La Granjita Pro - Historial Completo")
    st.markdown("Base de datos sincronizada con 4 días oficiales. Modifica o añade resultados directamente en la tabla.")

    # Panel lateral
    st.sidebar.header("Opciones")
    if st.sidebar.button("🔄 Restablecer Historial Oficial"):
        del st.session_state['df_sorteos']
        st.rerun()

    st.sidebar.success("✅ Historial de 4 días cargado correctamente.")

    # SECCIÓN DE EDICIÓN DIRECTA
    st.subheader("📝 Tabla de Sorteos Oficiales")
    st.markdown("💡 *Haz clic en la columna **Número** para completar los resultados de las 6:00 PM y 7:00 PM de hoy.*")

    df_editado = st.data_editor(
        st.session_state['df_sorteos'],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_sorteos_tabla_4dias"
    )

    for idx, row in df_editado.iterrows():
        num_limpio = str(row['Numero']).strip()
        if num_limpio in ANIMALES_MAP:
            df_editado.at[idx, 'Animal'] = ANIMALES_MAP[num_limpio]
        else:
            df_editado.at[idx, 'Animal'] = ""

    st.session_state['df_sorteos'] = df_editado

    df_analisis, ultimo_salido = ejecutar_motor_analisis(df_editado)

    # Mostrar último resultado
    st.markdown("---")
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.metric(label="Último Animal Activo", value=f"{ultimo_salido} - {ANIMALES_MAP.get(ultimo_salido, '')}")
    with col_u2:
        st.info(f"**💡 Análisis Jala-Jala Activo:** Último animal registrado: **{ultimo_salido} ({ANIMALES_MAP.get(ultimo_salido, '')})**. Con 4 días de historial, el motor tiene toda la data pesada lista.")

    st.markdown("---")

    # SECCIÓN 1: TOP 3 ZONA DULCE
    st.subheader("🎯 Top 3 Animalitos en 'Zona Dulce'")
    top_3 = df_analisis.head(3)
    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    
    for i, (idx, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"### #{i+1} - {row['Animal']}")
                st.markdown(f"**Puntuación Zona Dulce:** {row['Score_Zona_Dulce']:.1f}%")
                st.markdown(f"📊 Frecuencia: {row['Frecuencia']} | ⏳ Atraso: {row['Atraso']} sorteos")

    st.markdown("---")

    # SECCIÓN 2: TRIPLETA Y JUGADAS
    col_A, col_B = st.columns(2)

    with col_A:
        st.subheader("🔥 Tripleta Fuerte Recomendada")
        top_nums = df_analisis.index.tolist()
        if len(top_nums) >= 3:
            tripleta_principal = f"{top_nums[0]} ({ANIMALES_MAP[top_nums[0]]}) - {top_nums[1]} ({ANIMALES_MAP[top_nums[1]]}) - {top_nums[2]} ({ANIMALES_MAP[top_nums[2]]})"
            st.success(f"✨ **Tripleta Ideal:** {tripleta_principal}")
        else:
            st.warning("Faltan más datos para armar la tripleta.")

    with col_B:
        st.subheader("🎲 Jugadas Individuales Directas")
        df_individuales = df_analisis[['Animal', 'Frecuencia', 'Atraso', 'Score_Zona_Dulce']].head(5)
        df_individuales.columns = ['Animalito', 'Freq.', 'Atraso', 'Score %']
        st.dataframe(df_individuales, use_container_width=True)

if __name__ == '__main__':
    main()
