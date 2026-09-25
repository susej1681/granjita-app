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
    0: "LUNES", 1: "MARTES", 2: "MIÉRCOLES", 3: "JUEVES",
    4: "VIERNES", 5: "SÁBADO", 6: "DOMINGO"
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
                    hora_val = str(df_raw.iloc[fd, 0]).strip()
                    m = re.search(r'\((\d+)\)', val)
                    if m:
                        ns = m.group(1)
                        num = 100 if ns == "00" else int(ns)
                        nombre = ANIMALITOS_DICT.get(num, re.sub(r'\s*\(\d+\)', '', val).strip())
                        registros.append({
                            "fecha": fecha,
                            "hora": hora_val,
                            "numero": num,
                            "nombre": nombre
                        })
        df = pd.DataFrame(registros)
        if not df.empty:
            df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
            df = df.sort_values(["fecha_dt"], kind="stable").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(columns=["fecha", "hora", "numero", "nombre"])


def obtener_dias_ventana(hoy):
    dia_semana = hoy.weekday()
    if dia_semana == 0:  # LUNES
        sab = hoy - timedelta(days=2)
        dom = hoy - timedelta(days=1)
        return [sab, dom], "Referencia: Sábado + Domingo de la semana anterior"
    elif dia_semana == 1:  # MARTES
        dom = hoy - timedelta(days=2)
        lun = hoy - timedelta(days=1)
        return [dom, lun], "Referencia: Domingo anterior + Lunes"
    else:
        inicio = hoy - timedelta(days=dia_semana)
        dias = []
        d = inicio
        while d < hoy:
            dias.append(d)
            d += timedelta(days=1)
        return dias, f"Semana en curso: {len(dias)} días"


def mostrar_dia(df, fecha_obj):
    """Muestra todos los sorteos de un día con hora."""
    fecha_str = fecha_obj.strftime("%d/%m/%Y")
    nombre_dia = DIAS_SEMANA[fecha_obj.weekday()]
    
    df_dia = df[df["fecha"] == fecha_str].copy()
    if df_dia.empty:
        return False
    
    st.markdown(f"### 📅 {nombre_dia} {fecha_str}")
    
    # Ordenar por hora
    df_dia = df_dia.reset_index(drop=True)
    for i, row in df_dia.iterrows():
        hora = row.get("hora", "?")
        num = int(row["numero"])
        st.write(f"**{hora}** → {fmt_num(num)} {ANIMALITOS_DICT[num]}")
    
    st.markdown("")
    return True


def armar_5_tripletas(df_semana, excluidos_hoy):
    """El sistema arma 5 tripletas con los animalitos activos de la semana."""
    if df_semana.empty:
        return []
    
    # Contar apariciones y sus días
    apariciones = {}  # {num: {"total": X, "dias": set(), "ultima_aparicion": idx}}
    for idx, row in df_semana.iterrows():
        num = int(row["numero"])
        if num in excluidos_hoy:
            continue
        if num not in apariciones:
            apariciones[num] = {"total": 0, "dias": set(), "ultimo_idx": 0}
        apariciones[num]["total"] += 1
        apariciones[num]["dias"].add(row["fecha"])
        apariciones[num]["ultimo_idx"] = idx
    
    if len(apariciones) < 15:
        # Completar con los que no salieron (ni hoy)
        todos = [n for n in ANIMALITOS_DICT.keys() if n not in apariciones and n not in excluidos_hoy]
        for n in todos:
            if len(apariciones) >= 15:
                break
            apariciones[n] = {"total": 0, "dias": set(), "ultimo_idx": 0}
    
    # Ordenar por: total desc, ultimo_idx desc (más reciente primero)
    ordenados = sorted(apariciones.items(), 
                       key=lambda x: (x[1]["total"], x[1]["ultimo_idx"]), 
                       reverse=True)
    
    nums = [n for n, _ in ordenados]
    
    if len(nums) < 15:
        return []
    
    # Armar 5 tripletas combinando variado (sin repetidos dentro de cada una)
    tripletas = [
        [nums[0], nums[5], nums[9]],
        [nums[1], nums[3], nums[10]],
        [nums[2], nums[6], nums[12]],
        [nums[4], nums[7], nums[11]],
        [nums[8], nums[13], nums[14]],
    ]
    
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
    
    return resultado, apariciones


def main():
    st.title("📅 Tripletas Semanal")
    st.caption("Vista día por día · Con hora · 5 tripletas diarias")

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

    # Detectar qué salió HOY
    hoy_str = hoy.strftime("%d/%m/%Y")
    df_hoy = df[df["fecha"] == hoy_str]
    salieron_hoy = set(df_hoy["numero"].tolist())
    
    if salieron_hoy:
        st.warning(f"⚠️ **{len(salieron_hoy)} animalitos ya salieron hoy** (excluidos):")
        lista_hoy = ", ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in sorted(salieron_hoy)])
        st.caption(lista_hoy)

    # Obtener ventana de días
    dias_ventana, descripcion = obtener_dias_ventana(hoy)
    
    st.info(f"📊 **{descripcion}**")

    st.markdown("---")

    # ═══════════════════════════════════════
    # VISTA DÍA POR DÍA
    # ═══════════════════════════════════════
    st.markdown("## 📅 ANÁLISIS DÍA POR DÍA")

    dias_mostrados = 0
    for dia in dias_ventana:
        if mostrar_dia(df, dia):
            dias_mostrados += 1
    
    # Mostrar HOY también (los que han salido)
    if not df_hoy.empty:
        st.markdown(f"### 📅 {dia_nombre} {hoy_str} (HOY — parcial)")
        for i, row in df_hoy.iterrows():
            hora = row.get("hora", "?")
            num = int(row["numero"])
            st.write(f"**{hora}** → {fmt_num(num)} {ANIMALITOS_DICT[num]}")
        st.markdown("")

    if dias_mostrados == 0:
        st.warning("⚠️ No hay datos en la ventana actual.")
        return

    st.markdown("---")

    # ═══════════════════════════════════════
    # TRIPLETAS
    # ═══════════════════════════════════════
    st.markdown("## 🎯 5 TRIPLETAS PARA HOY")

    # Combinar toda la semana
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_ventana]
    df_semana = df[df["fecha"].isin(fechas_str)]

    resultado = armar_5_tripletas(df_semana, salieron_hoy)
    
    if not resultado or not resultado[0]:
        st.warning("No hay suficientes animalitos para armar las tripletas.")
        return
    
    tripletas, apariciones = resultado

    # Mostrar las 5 tripletas
    for i, trip in enumerate(tripletas, 1):
        nombres = " + ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in trip])
        if i <= 2:
            st.success(f"**Tripleta #{i}:** {nombres}")
        elif i == 3:
            st.info(f"**Tripleta #{i}:** {nombres}")
        else:
            st.warning(f"**Tripleta #{i}:** {nombres}")

    st.markdown("---")

    # Resumen de animalitos más activos
    with st.expander("📊 Ver animalitos más activos de la semana"):
        ordenados = sorted(apariciones.items(), key=lambda x: x[1]["total"], reverse=True)
        for num, info in ordenados[:20]:
            if info["total"] > 0:
                st.write(f"**{fmt_num(num)} {ANIMALITOS_DICT[num]}** — {info['total']} veces")

    st.caption("💡 Vista día por día con hora · Excluye los que ya salieron hoy")


if __name__ == "__main__":
    main()
