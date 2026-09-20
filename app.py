import streamlit as st
import pandas as pd
import re
from collections import Counter

st.set_page_config(
    page_title="Granjita Pro",
    page_icon="🐾",
    layout="centered"
)

GOOGLE_SHEET_ID = "1JpJgdyqu3HP4TlNyDocQ7WQjnsDfkUMP4Aj3q97TmHY"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"

SORTEOS_POR_DIA = 12
DIAS_VENTANA = 5
VENTANA_SORTEOS = SORTEOS_POR_DIA * DIAS_VENTANA
DESCARTE_ATRASO = 60

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
    if n == 100:
        return "00"
    if n == 0:
        return "0"
    return f"{n:02d}"


@st.cache_data(ttl=120)
def cargar_historial_google_sheets():
    try:
        df_raw = pd.read_csv(GOOGLE_SHEET_URL, header=None)
        filas_encabezado = []
        for fila in range(len(df_raw)):
            val = str(df_raw.iloc[fila, 0]).strip().lower()
            if val == "hora":
                filas_encabezado.append(fila)

        registros = []
        for idx, fila_enc in enumerate(filas_encabezado):
            if idx + 1 < len(filas_encabezado):
                fila_fin = filas_encabezado[idx + 1]
            else:
                fila_fin = len(df_raw)

            fechas_col = {}
            for col in range(1, len(df_raw.columns)):
                val = str(df_raw.iloc[fila_enc, col]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', val):
                    try:
                        fecha_dt = pd.to_datetime(val, format="%d/%m/%Y", errors="coerce")
                        if pd.notna(fecha_dt):
                            fechas_col[col] = fecha_dt.strftime("%d/%m/%Y")
                    except:
                        pass

            fila_fin_datos = min(fila_fin, fila_enc + 13)
            for col, fecha in fechas_col.items():
                for fila_dato in range(fila_enc + 1, fila_fin_datos):
                    val = str(df_raw.iloc[fila_dato, col]).strip()
                    if not val or val.lower() == "nan" or val.lower() == "hora":
                        continue
                    match = re.search(r'\((\d+)\)', val)
                    if match:
                        num_str = match.group(1)
                        num = 100 if num_str == "00" else int(num_str)
                        nombre = ANIMALITOS_DICT.get(num, re.sub(r'\s*\(\d+\)', '', val).strip())
                        registros.append({"fecha": fecha, "numero": num, "nombre": nombre})

        df = pd.DataFrame(registros)
        if not df.empty:
            df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
            df = df.sort_values(["fecha_dt"], kind="stable").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error al leer Google Sheet: {e}")
        return pd.DataFrame(columns=["fecha", "numero", "nombre"])


def aprender_jales(df, max_atraso=3):
    jales = {n: Counter() for n in ANIMALITOS_DICT.keys()}
    nums = df["numero"].tolist()
    for i in range(len(nums) - 1):
        origen = nums[i]
        for j in range(i + 1, min(i + 1 + max_atraso, len(nums))):
            jales[origen][nums[j]] += 1
    return jales


def detectar_alineaciones(df, min_repeticiones=2):
    nums = df["numero"].tolist()
    total = len(nums)
    alineaciones = []
    for i in range(total - 10):
        ventana = nums[i:i + 5]
        unicos = list(dict.fromkeys(ventana))
        for a in range(len(unicos)):
            for b in range(a + 1, len(unicos)):
                alineaciones.append(tuple(sorted([unicos[a], unicos[b]])))
    conteo = Counter(alineaciones)
    parejas_top = [p for p, c in conteo.most_common(5) if c >= min_repeticiones]
    resultado = []
    for par in parejas_top:
        posiciones = []
        for i in range(total - 5):
            ventana = set(nums[i:i + 5])
            if par[0] in ventana and par[1] in ventana:
                posiciones.append(i)
        if len(posiciones) >= 2:
            ultima = posiciones[-1]
            atraso = total - 1 - ultima
            diffs = [posiciones[k + 1] - posiciones[k] for k in range(len(posiciones) - 1)]
            promedio = sum(diffs) / len(diffs) if diffs else 0
            if promedio > 0 and atraso >= promedio * 0.6:
                resultado.append({"par": par, "veces": len(posiciones), "atraso": atraso, "promedio": round(promedio, 1)})
    return resultado


def calcular_ritmo_historico(df):
    nums = df["numero"].tolist()
    ritmos = {}
    for num in ANIMALITOS_DICT.keys():
        posiciones = [i for i, n in enumerate(nums) if n == num]
        if len(posiciones) >= 2:
            diffs = [posiciones[k + 1] - posiciones[k] for k in range(len(posiciones) - 1)]
            ritmos[num] = {"promedio": round(sum(diffs) / len(diffs), 1), "veces_total": len(posiciones), "apariciones": posiciones}
        else:
            ritmos[num] = {"promedio": 999, "veces_total": len(posiciones), "apariciones": posiciones}
    return ritmos


def calcular_fijo_del_dia(df, scores, detalles, ritmos):
    """Calcula el Fijo del Día respetando el filtro de enjaulados."""
    total = len(df)
    candidatos = []
    for num in ANIMALITOS_DICT.keys():
        if num not in ritmos or ritmos[num]["promedio"] >= 500:
            continue
        posiciones = ritmos[num]["apariciones"]
        if not posiciones:
            continue

        atraso_actual = total - 1 - posiciones[-1]

        # FILTRO: NO recomendar enjaulados
        if atraso_actual >= DESCARTE_ATRASO:
            continue

        ritmo = ritmos[num]["promedio"]
        if ritmo <= 0:
            continue

        ratio = atraso_actual / ritmo
        if ratio >= 1.5:
            prob = 0.85
        elif ratio >= 1.0:
            prob = 0.70
        elif ratio >= 0.7:
            prob = 0.55
        elif ratio >= 0.5:
            prob = 0.40
        else:
            prob = 0.20

        if ratio > 4:
            prob *= 0.5

        if detalles[num]["atraso_hoy"] <= 1:
            prob *= 0.3

        candidatos.append({
            "num": num, "prob": prob, "atraso": atraso_actual,
            "ritmo": ritmo, "ratio": round(ratio, 2),
            "score": scores.get(num, 0)
        })
    candidatos.sort(key=lambda x: (x["prob"], x["score"]), reverse=True)
    return candidatos[0] if candidatos else None


def motor_casi_adivino(df):
    if df.empty or len(df) < 60:
        return {}, {}, None, [], [], None, {}, {}

    df_ventana = df.tail(VENTANA_SORTEOS).copy()
    freq_ventana = Counter(df_ventana["numero"].tolist())
    freq_rec20 = Counter(df.tail(20)["numero"].tolist())
    freq_rec30 = Counter(df.tail(30)["numero"].tolist())

    atrasos = {}
    total = len(df)
    for num in ANIMALITOS_DICT.keys():
        idxs = df[df["numero"] == num].index.tolist()
        atrasos[num] = total - 1 - idxs[-1] if idxs else total

    fecha_hoy = df["fecha"].iloc[-1]
    df_hoy = df[df["fecha"] == fecha_hoy]
    total_hoy = len(df_hoy)
    atraso_hoy = {}
    for num in ANIMALITOS_DICT.keys():
        idxs_hoy = df_hoy[df_hoy["numero"] == num].index.tolist()
        if idxs_hoy:
            pos = df_hoy.index.get_loc(idxs_hoy[-1])
            atraso_hoy[num] = total_hoy - 1 - pos
        else:
            atraso_hoy[num] = 999

    jales_aprendidos = aprender_jales(df, max_atraso=3)

    ultimos_10 = df.tail(10)["numero"].tolist()
    jales_entrantes = Counter()
    for nr in ultimos_10:
        for siguiente, c in jales_aprendidos.get(nr, Counter()).most_common(3):
            jales_entrantes[siguiente] += c

    max_fv = max(freq_ventana.values()) if freq_ventana else 1
    max_f20 = max(freq_rec20.values()) if freq_rec20 else 1
    max_atr = max(atrasos.values()) if atrasos else 1
    max_jal = max(jales_entrantes.values()) if jales_entrantes else 1

    fechas_unicas = df["fecha"].unique().tolist()
    ultima_fecha_str = fechas_unicas[-1]
    ultima_fecha_dt = pd.to_datetime(ultima_fecha_str, format="%d/%m/%Y", errors="coerce")
    hoy_real_dt = pd.Timestamp.now().normalize()

    fecha_dia_anterior = None
    if pd.notna(ultima_fecha_dt):
        if ultima_fecha_dt.normalize() == hoy_real_dt:
            if len(fechas_unicas) >= 2:
                fecha_dia_anterior = fechas_unicas[-2]
        else:
            fecha_dia_anterior = ultima_fecha_str

    scores = {}
    detalles = {}

    for num in ANIMALITOS_DICT.keys():
        fv = freq_ventana.get(num, 0)
        f20 = freq_rec20.get(num, 0)
        f30 = freq_rec30.get(num, 0)
        atr = atrasos.get(num, 0)
        atr_hoy = atraso_hoy.get(num, 999)
        jal = jales_entrantes.get(num, 0)

        n_fv = fv / max_fv if max_fv else 0
        n_f20 = f20 / max_f20 if max_f20 else 0
        n_atr = atr / max_atr if max_atr else 0
        n_jal = jal / max_jal if max_jal else 0

        bonus_caliente = 0.08 if f30 >= 3 else (0.04 if f30 == 2 else 0)
        penal_frio = 0
        if atr > 60:
            penal_frio = -0.35
        elif atr > 45:
            penal_frio = -0.20
        elif atr > 30:
            penal_frio = -0.10

        penal_reciente = 0
        if atr_hoy == 0:
            penal_reciente = -0.60
        elif atr_hoy == 1:
            penal_reciente = -0.45
        elif atr_hoy == 2:
            penal_reciente = -0.30
        elif atr_hoy == 3:
            penal_reciente = -0.20
        elif atr_hoy == 4:
            penal_reciente = -0.10

        score = (
            n_fv * 0.25 + n_f20 * 0.25 + n_atr * 0.20 +
            n_jal * 0.15 + bonus_caliente + penal_frio + penal_reciente
        )

        if fv == 0:
            score *= 0.4

        # FILTRO: enjaulados tienen score 0
        if atr >= DESCARTE_ATRASO:
            score = 0

        scores[num] = round(max(score, 0) * 100, 2)
        detalles[num] = {
            "freq_ventana": fv, "freq_20": f20, "atraso": atr,
            "atraso_hoy": atr_hoy, "jales_in": jal,
            "caliente": bonus_caliente > 0, "penal": penal_frio < 0,
            "reciente": penal_reciente < 0, "enjaulado": atr >= DESCARTE_ATRASO
        }

    top_ordenado = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    alineaciones = detectar_alineaciones(df, min_repeticiones=2)
    ritmos = calcular_ritmo_historico(df)

    return scores, detalles, top_ordenado, jales_aprendidos, alineaciones, fecha_dia_anterior, atrasos, ritmos


def armar_resultados(scores, detalles, top_ordenado, atrasos):
    # Solo los que NO están enjaulados
    top_validos = [(n, s) for n, s in top_ordenado if not detalles[n]["enjaulado"]]

    top3 = []
    for num, sc in top_validos[:3]:
        top3.append({"numero": fmt_num(num), "int_num": num, "nombre": ANIMALITOS_DICT[num], "score": sc, "detalle": detalles[num]})

    individual = top3[0] if top3 else None

    nums_oficiales = set([t["int_num"] for t in top3])
    candidatos = [(n, s) for n, s in top_validos if n not in nums_oficiales and s > 0][:20]

    caliente = None
    for n, s in candidatos:
        if detalles[n]["freq_20"] >= 2:
            caliente = n
            break
    if caliente is None and candidatos:
        caliente = candidatos[0][0]

    maduro = None
    for n, s in candidatos:
        if n == caliente: continue
        atr = atrasos.get(n, 0)
        if 10 <= atr <= 55:
            maduro = n
            break
    if maduro is None:
        for n, s in candidatos:
            if n != caliente:
                maduro = n
                break

    jale = None
    for n, s in candidatos:
        if n in (caliente, maduro): continue
        if detalles[n]["jales_in"] >= 2:
            jale = n
            break
    if jale is None:
        for n, s in candidatos:
            if n not in (caliente, maduro):
                jale = n
                break

    t_alt = [n for n in [caliente, maduro, jale] if n is not None]
    for n, s in candidatos:
        if len(t_alt) >= 3: break
        if n not in t_alt:
            t_alt.append(n)

    tripleta_alt = []
    for num in t_alt[:3]:
        tripleta_alt.append({"numero": fmt_num(num), "int_num": num, "nombre": ANIMALITOS_DICT[num], "score": scores[num], "detalle": detalles[num]})

    return individual, top3, tripleta_alt


def main():
    st.title("🐾 Granjita Pro")
    st.caption("Fijo · Tripletas · Filtro de enjaulados (60+ sorteos descartados)")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Leyendo hoja de cálculo..."):
        df = cargar_historial_google_sheets()

    if df.empty:
        st.error("No se pudieron cargar datos.")
        return

    scores, detalles, top_ordenado, jales_aprendidos, alineaciones, fecha_dia_anterior, atrasos, ritmos = motor_casi_adivino(df)
    if not top_ordenado:
        st.warning("Datos insuficientes.")
        return

    individual, top3, tripleta_alt = armar_resultados(scores, detalles, top_ordenado, atrasos)
    ultimo = df.iloc[-1]

    # FIJO DEL DÍA
    fijo = calcular_fijo_del_dia(df, scores, detalles, ritmos)
    if fijo:
        st.markdown("### 🎯 FIJO DEL DÍA")
        st.markdown(f"## {fmt_num(fijo['num'])} - {ANIMALITOS_DICT[fijo['num']]}")
        st.markdown(f"**Probabilidad estimada: {round(fijo['prob']*100, 1)}%**")
        st.caption(f"Atraso: {fijo['atraso']} · Ritmo: cada {fijo['ritmo']} sorteos · Ratio: {fijo['ratio']}")
        st.markdown("---")

    # ALINEACIONES
    if alineaciones:
        st.markdown("### 🔗 Alineación Caliente")
        for al in alineaciones[:3]:
            a, b = al["par"]
            if detalles.get(a, {}).get("enjaulado") or detalles.get(b, {}).get("enjaulado"):
                continue
            st.markdown(f"**{fmt_num(a)} {ANIMALITOS_DICT[a]} + {fmt_num(b)} {ANIMALITOS_DICT[b]}**")
            st.caption(f"{al['veces']} veces · Promedio cada {al['promedio']} · Atraso: {al['atraso']}")
        st.markdown("---")

    st.markdown("### 🎯 Último resultado")
    st.markdown(f"## {fmt_num(int(ultimo['numero']))} - {ultimo['nombre']}")
    st.caption(f"Fecha: {ultimo['fecha']}")
    st.markdown("---")

    if fecha_dia_anterior:
        st.markdown(f"### 🔁 Animales del {fecha_dia_anterior}")
        df_dia = df[df["fecha"] == fecha_dia_anterior].reset_index(drop=True)
        for i, row in df_dia.iterrows():
            num = int(row["numero"])
            d = detalles.get(num, {})
            st.write(f"{i+1}. **{fmt_num(num)} - {row['nombre']}** (atraso: {d.get('atraso', '?')})")
        st.markdown("---")

    if individual:
        st.markdown("### 🎯 Animal Individual")
        d = individual["detalle"]
        st.markdown(f"## {individual['numero']} - {individual['nombre']}")
        st.markdown(f"**Score: {individual['score']}%**")
        st.caption(f"Freq(60): {d['freq_ventana']} | Freq(20): {d['freq_20']} | Atraso: {d['atraso']} | Jales: {d['jales_in']}")
        st.markdown("---")

    st.markdown("### 🏆 Top 3")
    if top3:
        for i, item in enumerate(top3, 1):
            d = item["detalle"]
            st.markdown(f"**#{i} - {item['numero']} {item['nombre']}** — {item['score']}%")
            st.caption(f"Freq(60): {d['freq_ventana']} | Freq(20): {d['freq_20']} | Atraso: {d['atraso']} | Jales: {d['jales_in']}")
    else:
        st.warning("No hay animalitos válidos (todos enjaulados o sin datos).")
    st.markdown("---")

    st.markdown("### 🎯 Tripleta OFICIAL (cubre 11 sorteos)")
    if len(top3) >= 3:
        st.success(" - ".join([f"{t['numero']} {t['nombre']}" for t in top3]))
    else:
        st.warning("No hay suficientes animalitos válidos.")
    st.markdown("---")

    st.markdown("### ⚡ Tripleta ALTERNATIVA (cubre 11 sorteos)")
    if len(tripleta_alt) >= 3:
        st.info(" - ".join([f"{t['numero']} {t['nombre']}" for t in tripleta_alt]))
    else:
        st.warning("No hay suficientes animalitos válidos.")
    st.markdown("---")

    st.markdown("### 🔗 Jales Aprendidos (Top 3 del último resultado)")
    ultimo_num = int(ultimo["numero"])
    jales_ult = jales_aprendidos.get(ultimo_num, Counter())
    if jales_ult:
        for jale, c in jales_ult.most_common(3):
            if detalles.get(jale, {}).get("enjaulado"):
                continue
            st.write(f"- Después de **{fmt_num(ultimo_num)} {ultimo['nombre']}** → **{fmt_num(jale)} {ANIMALITOS_DICT[jale]}** ({c} veces)")

    with st.expander("📋 Ver últimos 30 sorteos"):
        st.dataframe(df.tail(30)[["fecha", "numero", "nombre"]], use_container_width=True)


if __name__ == "__main__":
    main()
