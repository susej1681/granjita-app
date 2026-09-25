import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Tripletas Semanal",
    page_icon="📅",
    layout="centered"
)

GOOGLE_SHEET_ID = "1JpJgdyqu3HP4TlNyDocQ7WQjnsDfkUMP4Aj3q97TmHY"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

ANIMALITOS_DICT = {
    0: "Delfín", 1: "Carnero", 2: "Toro", 3: "Ciempiés", 4: "Alacrán",
    5: "León", 6: "Rana", 7: "Perico", 8: "Ratón", 9: "Águila",
    10: "Tigre", 11: "Gato", 12: "Caballo", 13: "Mono", 14: "Paloma",
    15: "Zorro", 16: "Oso", 17: "Pavo", 18: "Burro", 19: "Chivo",
    20: "Cochino", 21: "Gallo", 22: "Camello", 23: "Cebra", 24: "Iguana",
    25: "Gallina", 26: "Vaca", 27: "Perro", 28: "Zamuro", 29: "Elefante",
    30: "Caimán", 31: "Lapa", 32: "Ardilla", 33: "Pescado", 34: "Venado",
    35: "Jirafa", 36: "Culebra", 100: "Ballena"
}


def fmt_num(n):
    if n == 100: return "00"
    if n == 0: return "0"
    return f"{n:02d}"


@st.cache_data(ttl=120)
def cargar_historial():
    try:
        df_raw = pd.read_csv(GOOGLE_SHEET_URL, header=None)
        filas_enc = []
        for fila in range(len(df_raw)):
            val = str(df_raw.iloc[fila, 0]).strip().lower()
            if val == "hora":
                filas_enc.append(fila)
        registros = []
        for idx, fe in enumerate(filas_enc):
            ff = filas_enc[idx + 1] if idx + 1 < len(filas_enc) else len(df_raw)
            fechas_col = {}
            for col in range(1, len(df_raw.columns)):
                val = str(df_raw.iloc[fe, col]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', val):
                    try:
                        fd = pd.to_datetime(val, format="%d/%m/%Y", errors="coerce")
                        if pd.notna(fd):
                            fechas_col[col] = fd.strftime("%d/%m/%Y")
                    except:
                        pass
            ff_datos = min(ff, fe + 13)
            for col, fecha in fechas_col.items():
                for fd in range(fe + 1, ff_datos):
                    val = str(df_raw.iloc[fd, col]).strip()
                    if not val or val.lower() == "nan" or val.lower() == "hora":
                        continue
                    m = re.search(r'\((\d+)\)', val)
                    if m:
                        ns = m.group(1)
                        num = 100 if ns == "00" else int(ns)
                        nombre = ANIMALITOS_DICT.get(num, re.sub(r'\s*\(\d+\)', '', val).strip())
                        registros.append({"fecha": fecha, "numero": num, "nombre": nombre})
        df = pd.DataFrame(registros)
        if not df.empty:
            df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
            df = df.sort_values(["fecha_dt"], kind="stable").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(columns=["fecha", "numero", "nombre"])


def obtener_dias_ventana(hoy):
    """Devuelve los días de la semana que entran en la ventana según qué día es hoy."""
    dia_semana = hoy.weekday()  # 0=lunes, 6=domingo
    
    if dia_semana == 0:  # LUNES
        # Referencia: sábado y domingo de la semana pasada
        sab = hoy - timedelta(days=2)
        dom = hoy - timedelta(days=1)
        return [sab, dom], "Referencia: Sáb + Dom semana anterior"
    
    elif dia_semana == 1:  # MARTES
        # Referencia: domingo pasado + lunes
        dom = hoy - timedelta(days=2)
        lun = hoy - timedelta(days=1)
        return [dom, lun], "Referencia: Dom anterior + Lunes"
    
    else:  # MIÉRCOLES a DOMINGO
        # Todos los días desde el lunes de esta semana hasta ayer
        inicio_semana = hoy - timedelta(days=dia_semana)
        dias = []
        d = inicio_semana
        while d < hoy:
            dias.append(d)
            d += timedelta(days=1)
        return dias, f"Semana en curso: {len(dias)} días"


def analizar_semana(df, dias_ventana):
    """Analiza los animalitos que salieron en la ventana."""
    if not dias_ventana:
        return Counter(), []
    
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_ventana]
    df_ventana = df[df["fecha"].isin(fechas_str)]
    
    if df_ventana.empty:
        return Counter(), []
    
    conteo = Counter(df_ventana["numero"].tolist())
    ordenados = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    
    return conteo, ordenados


def armar_5_tripletas(ordenados):
    """Arma 5 tripletas con la Opción D (mezcla variada)."""
    if len(ordenados) < 15:
        # Si hay menos de 15, usar todos los disponibles
        nums = [n for n, _ in ordenados]
        if len(nums) < 3:
            return []
        # Rellenar con fríos si es necesario
        todos_frios = [n for n in ANIMALITOS_DICT.keys() if n not in nums]
        while len(nums) < 15 and todos_frios:
            nums.append(todos_frios.pop(0))
    else:
        nums = [n for n, _ in ordenados[:15]]
    
    if len(nums) < 15:
        return []
    
    # Opción D: mezcla variada
    tripletas = [
        [nums[0], nums[5], nums[9]],    # T1: 1 top + 2 medios
        [nums[0], nums[1], nums[10]],   # T2: 2 top + 1 medio
        [nums[2], nums[3], nums[6]],    # T3: 3 medios
        [nums[7], nums[11], nums[14]],  # T4: 1 frío + 2 medios
        [nums[12], nums[13], nums[4]],  # T5: 3 fríos (con 1 medio)
    ]
    
    # Asegurar que no hay repetidos dentro de cada tripleta
    resultado = []
    for t in tripletas:
        vistos = set()
        unicos = []
        for n in t:
            if n not in vistos:
                unicos.append(n)
                vistos.add(n)
        if len(unicos) == 3:
            resultado.append(unicos)
    
    return resultado


def main():
    st.title("📅 Tripletas Semanal")
    st.caption("Ventana creciente de lunes a domingo · 5 tripletas diarias")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Leyendo hoja..."):
        df = cargar_historial()

    if df.empty:
        st.error("No se pudieron cargar datos.")
        return

    # Fecha automática
    hoy = datetime.now().date()
    dia_nombre = DIAS_SEMANA[hoy.weekday()]
    
    st.markdown(f"## 📅 Hoy es **{dia_nombre}**")
    st.caption(f"Fecha: {hoy.strftime('%d/%m/%Y')}")

    # Obtener ventana de días
    dias_ventana, descripcion = obtener_dias_ventana(hoy)
    
    st.info(f"📊 **{descripcion}**")
    if dias_ventana:
        dias_str = " · ".join([d.strftime("%d/%m") for d in dias_ventana])
        st.caption(f"Días incluidos: {dias_str}")

    st.markdown("---")

    # Analizar ventana
    conteo, ordenados = analizar_semana(df, dias_ventana)
    
    if not conteo:
        st.warning("⚠️ No hay datos en la ventana actual. Necesitas al menos 1 día de resultados.")
        st.info("💡 El lunes usa sáb+dom de la semana pasada. El martes usa dom+lun. Desde miércoles usa la semana en curso.")
        return

    # Mostrar lista completa
    st.markdown("## 📊 Animalitos de la ventana")
    st.caption(f"Total: {len(ordenados)} animalitos salieron")
    
    for i, (num, veces) in enumerate(ordenados, 1):
        st.write(f"{i}. **{fmt_num(num)} {ANIMALITOS_DICT[num]}** — {veces} veces")

    st.markdown("---")

    # Armar las 5 tripletas
    st.markdown("## 🎯 5 TRIPLETAS PARA HOY")
    
    tripletas = armar_5_tripletas(ordenados)
    
    if not tripletas:
        st.warning("No hay suficientes animalitos para armar las tripletas.")
        return
    
    for i, trip in enumerate(tripletas, 1):
        nombres = " + ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in trip])
        if i <= 2:
            st.success(f"**Tripleta #{i}:** {nombres}")
        elif i == 3:
            st.info(f"**Tripleta #{i}:** {nombres}")
        else:
            st.warning(f"**Tripleta #{i}:** {nombres}")

    st.markdown("---")
    st.caption("💡 Las tripletas se arman con los animalitos que salieron en la ventana · Repetidos entre tripletas permitidos · Sin repetidos dentro de la misma tripleta")


if __name__ == "__main__":
    main()
