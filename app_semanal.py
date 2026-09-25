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
    0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue",
    4: "Vie", 5: "Sáb", 6: "Dom"
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
    dia_semana = hoy.weekday()
    if dia_semana == 0:  # LUNES
        sab = hoy - timedelta(days=2)
        dom = hoy - timedelta(days=1)
        return [sab, dom], "Referencia: Sáb + Dom semana anterior"
    elif dia_semana == 1:  # MARTES
        dom = hoy - timedelta(days=2)
        lun = hoy - timedelta(days=1)
        return [dom, lun], "Referencia: Dom anterior + Lunes"
    else:
        inicio = hoy - timedelta(days=dia_semana)
        dias = []
        d = inicio
        while d < hoy:
            dias.append(d)
            d += timedelta(days=1)
        return dias, f"Semana en curso: {len(dias)} días"


def construir_tabla_semanal(df, dias_ventana):
    """Construye una tabla de animalitos x días."""
    if not dias_ventana:
        return {}, []
    
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_ventana]
    df_ventana = df[df["fecha"].isin(fechas_str)]
    
    if df_ventana.empty:
        return {}, []
    
    # Tabla: {animalito: {fecha: veces}}
    tabla = {}
    for _, row in df_ventana.iterrows():
        num = row["numero"]
        fecha = row["fecha"]
        if num not in tabla:
            tabla[num] = {}
        tabla[num][fecha] = tabla[num].get(fecha, 0) + 1
    
    # Ordenar por total de apariciones
    ordenados = sorted(tabla.items(), 
                       key=lambda x: sum(x[1].values()), 
                       reverse=True)
    
    return tabla, ordenados


def armar_5_tripletas(animalitos_activos, excluidos_hoy):
    """Arma 5 tripletas con los animalitos activos (sin fríos ni calientes, todos iguales)."""
    # Filtrar los que ya salieron hoy
    nums = [n for n in animalitos_activos if n not in excluidos_hoy]
    
    # Completar si faltan
    if len(nums) < 15:
        todos = [n for n in ANIMALITOS_DICT.keys() 
                 if n not in nums and n not in excluidos_hoy]
        while len(nums) < 15 and todos:
            nums.append(todos.pop(0))
    
    if len(nums) < 15:
        return []
    
    # Opción D: mezcla variada (usando el orden de actividad)
    tripletas = [
        [nums[0], nums[5], nums[9]],
        [nums[1], nums[3], nums[10]],
        [nums[2], nums[6], nums[12]],
        [nums[4], nums[7], nums[11]],
        [nums[8], nums[13], nums[14]],
    ]
    
    # Sin repetidos dentro de cada tripleta
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
    st.caption("Análisis día por día · Sin fríos ni calientes · Todos iguales")

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
    dia_nombre = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][hoy.weekday()]
    
    st.markdown(f"## 📅 Hoy es **{dia_nombre}**")
    st.caption(f"Fecha: {hoy.strftime('%d/%m/%Y')}")

    # Detectar qué salió HOY
    hoy_str = hoy.strftime("%d/%m/%Y")
    df_hoy = df[df["fecha"] == hoy_str]
    salieron_hoy = set(df_hoy["numero"].tolist())
    
    if salieron_hoy:
        st.warning(f"⚠️ **{len(salieron_hoy)} animalitos ya salieron hoy** (quedan excluidos):")
        lista_hoy = ", ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in sorted(salieron_hoy)])
        st.caption(lista_hoy)

    # Obtener ventana de días
    dias_ventana, descripcion = obtener_dias_ventana(hoy)
    
    st.info(f"📊 **{descripcion}**")
    if dias_ventana:
        dias_str = " · ".join([d.strftime("%d/%m") for d in dias_ventana])
        st.caption(f"Días incluidos: {dias_str}")

    st.markdown("---")

    # Construir tabla semanal
    tabla, ordenados = construir_tabla_semanal(df, dias_ventana)
    
    if not tabla:
        st.warning("⚠️ No hay datos en la ventana actual.")
        return

    # Mostrar tabla día por día
    st.markdown("## 📊 ANÁLISIS DÍA POR DÍA")
    st.caption("Ve qué animalito salió cada día de la semana")
    
    # Headers
    headers = "| Animalito | " + " | ".join([DIAS_SEMANA[d.weekday()] for d in dias_ventana]) + " | Total |"
    st.markdown("**" + headers + "**")
    st.markdown("|" + "---|" * (len(dias_ventana) + 2))
    
    for num, dias_dict in ordenados:
        total = sum(dias_dict.values())
        if num in salieron_hoy:
            continue  # No mostrar los que salieron hoy
        fila = f"| {fmt_num(num)} {ANIMALITOS_DICT[num]} |"
        for d in dias_ventana:
            fecha_str = d.strftime("%d/%m/%Y")
            veces = dias_dict.get(fecha_str, 0)
            if veces > 0:
                fila += f" ✅{veces if veces > 1 else ''} |"
            else:
                fila += " ❌ |"
        fila += f" {total} |"
        st.markdown(fila)

    st.markdown("---")

    # Armar las 5 tripletas
    st.markdown("## 🎯 5 TRIPLETAS PARA HOY")
    st.caption("Combinando animalitos activos de la semana (sin los que ya salieron hoy)")
    
    animalitos_activos = [n for n, _ in ordenados]
    tripletas = armar_5_tripletas(animalitos_activos, salieron_hoy)
    
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
    st.caption("💡 Análisis día por día · Sin fríos ni calientes · Excluye los que ya salieron hoy")


if __name__ == "__main__":
    main()
