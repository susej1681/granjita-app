import streamlit as st
import pandas as pd
import re
from collections import Counter
from itertools import combinations

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

SERIES = {
    "Serie 0 (00-09)": list(range(0, 10)),
    "Serie 10 (10-19)": list(range(10, 20)),
    "Serie 20 (20-29)": list(range(20, 30)),
    "Serie 30 (30-36)": list(range(30, 37)) + [100]
}


def fmt_num(n):
    if n == 100: return "00"
    if n == 0: return "0"
    return f"{n:02d}"


def serie_de(num):
    for nombre, lista in SERIES.items():
        if num in lista:
            return nombre
    return "?"


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
            fila_fin = filas_encabezado[idx + 1] if idx + 1 < len(filas_encabezado) else len(df_raw)
            fechas_col = {}
            for col in range(1, len(df_raw.columns)):
                val = str(df_raw.iloc[fila_enc, col]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', val):
                    try:
                        fecha_dt = pd.to_datetime(val, format="%d/%m/%Y", errors="coerce")
                        if pd.notna(fecha_dt):
                            fechas_col[col] = fecha_dt.strftime("%d/%m/%Y")
                    except: pass
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
        st.error(f"Error: {e}")
        return pd.DataFrame(columns=["fecha", "numero", "nombre"])


def aprender_cadenas(df, max_salto=3):
    cadenas = {n: Counter() for n in ANIMALITOS_DICT.keys()}
    nums = df["numero"].tolist()
    for i in range(len(nums) - 1):
        origen = nums[i]
        for j in range(i + 1, min(i + 1 + max_salto, len(nums))):
            cadenas[origen][nums[j]] += 1
    return cadenas


def buscar_trios_historicos(df, dias_analisis=60, min_repeticiones=2, ventana=11):
    if df.empty or len(df) < ventana:
        return []
    fechas_unicas = sorted(df["fecha_dt"].unique())
    if len(fechas_unicas) > dias_analisis:
        fecha_min = fechas_unicas[-dias_analisis]
        df = df[df["fecha_dt"] >= fecha_min].reset_index(drop=True)
    nums = df["numero"].tolist()
    total = len(nums)
    if total < ventana:
        return []
    conteo_trios = Counter()
    for i in range(total - ventana + 1):
        ventana_nums = nums[i:i + ventana]
        unicos = list(set(ventana_nums))
        if len(unicos) < 3:
            continue
        for trio in combinations(sorted(unicos), 3):
            conteo_trios[trio] += 1
    trios_filtrados = [(t, c) for t, c in conteo_trios.items() if c >= min_repeticiones]
    trios_filtrados.sort(key=lambda x: x[1], reverse=True)
    return trios_filtrados[:50]


def calcular_tripleta_pensante(df, detalles, scores, ritmos, cadenas, trios_hist, salieron_hoy, excluir=None):
    if excluir is None:
        excluir = set()

    candidatos_1 = []
    for num in ANIMALITOS_DICT.keys():
        if num in salieron_hoy or num in excluir: continue
        if detalles[num]["enjaulado"]: continue
        if num not in ritmos or ritmos[num]["promedio"] >= 500: continue
        pos = ritmos[num]["apariciones"]
        if not pos: continue
        atraso = len(df) - 1 - pos[-1]
        ritmo = ritmos[num]["promedio"]
        if ritmo <= 0: continue
        ratio = atraso / ritmo
        if ratio >= 1.5: prob = 0.85
        elif ratio >= 1.0: prob = 0.70
        elif ratio >= 0.7: prob = 0.55
        elif ratio >= 0.5: prob = 0.40
        else: prob = 0.20
        if ratio > 4: prob *= 0.5
        if detalles[num]["atraso_hoy"] <= 1: prob *= 0.3
        score_final = prob * 100 + scores.get(num, 0) * 0.3
        candidatos_1.append({"num": num, "score": score_final, "atraso": atraso, "ritmo": ritmo, "ratio": round(ratio, 2), "prob": prob})

    candidatos_1.sort(key=lambda x: x["score"], reverse=True)
    if not candidatos_1:
        return None, []
    cand1 = candidatos_1[0]
    num1 = cand1["num"]

    explicaciones = [f"🎯 **{fmt_num(num1)} {ANIMALITOS_DICT[num1]}**: atraso {cand1['atraso']} vs ritmo {cand1['ritmo']} (ratio {cand1['ratio']})"]

    cadena_1 = cadenas.get(num1, Counter())
    candidatos_2 = []
    for num2, veces in cadena_1.most_common(20):
        if num2 == num1 or num2 in salieron_hoy or num2 in excluir: continue
        if detalles[num2]["enjaulado"]: continue
        score_cad = veces * 10
        if 3 <= detalles[num2]["atraso"] <= 40:
            score_cad += 15
        score_cad += detalles[num2]["freq_20"] * 5
        candidatos_2.append({"num": num2, "score": score_cad, "veces": veces, "atraso": detalles[num2]["atraso"]})

    if len(candidatos_2) < 1:
        for c in candidatos_1[1:]:
            if c["num"] not in salieron_hoy and c["num"] not in excluir:
                candidatos_2.append({"num": c["num"], "score": c["score"], "veces": 0, "atraso": c["atraso"]})
                break

    if not candidatos_2:
        return None, []
    candidatos_2.sort(key=lambda x: x["score"], reverse=True)
    num2 = candidatos_2[0]["num"]
    veces_2 = candidatos_2[0]["veces"]
    if veces_2 > 0:
        explicaciones.append(f"🔗 **{fmt_num(num2)} {ANIMALITOS_DICT[num2]}**: después de {ANIMALITOS_DICT[num1]} ha salido {veces_2} veces (atraso {candidatos_2[0]['atraso']})")
    else:
        explicaciones.append(f"📊 **{fmt_num(num2)} {ANIMALITOS_DICT[num2]}**: segundo más maduro (atraso {candidatos_2[0]['atraso']})")

    candidatos_3 = []
    for num3 in ANIMALITOS_DICT.keys():
        if num3 in (num1, num2) or num3 in salieron_hoy or num3 in excluir: continue
        if detalles[num3]["enjaulado"]: continue

        score_3 = 0
        explicacion_3 = []

        for trio, veces in trios_hist[:30]:
            if num3 in trio and num1 in trio and num2 in trio:
                score_3 += veces * 25
                explicacion_3.append(f"trío histórico ({veces} veces)")

        c1 = cadenas.get(num1, Counter()).get(num3, 0)
        c2 = cadenas.get(num2, Counter()).get(num3, 0)
        if c1 > 0 or c2 > 0:
            score_3 += (c1 + c2) * 5
            explicacion_3.append(f"cadenas ({c1 + c2})")

        if 3 <= detalles[num3]["atraso"] <= 40:
            score_3 += 15
            explicacion_3.append(f"atraso {detalles[num3]['atraso']}")

        score_3 += detalles[num3]["jales_in"] * 4

        if serie_de(num3) != serie_de(num1) and serie_de(num3) != serie_de(num2):
            score_3 += 8
            explicacion_3.append("otra serie")

        if score_3 > 0:
            candidatos_3.append({"num": num3, "score": score_3, "razon": ", ".join(explicacion_3) if explicacion_3 else "complementario"})

    candidatos_3.sort(key=lambda x: x["score"], reverse=True)
    if not candidatos_3:
        return None, []
    num3 = candidatos_3[0]["num"]
    explicaciones.append(f"🧩 **{fmt_num(num3)} {ANIMALITOS_DICT[num3]}**: {candidatos_3[0]['razon']}")

    return [num1, num2, num3], explicaciones


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
            ritmos[num] = {"promedio": round(sum(diffs) / len(diffs), 1), "apariciones": posiciones}
        else:
            ritmos[num] = {"promedio": 999, "apariciones": posiciones}
    return ritmos


def calcular_ultimo_dia(df):
    if df.empty:
        return None, set()
    fecha_hoy = df["fecha"].iloc[-1]
    df_hoy = df[df["fecha"] == fecha_hoy]
    return fecha_hoy, set(df_hoy["numero"].tolist())


def analizar_series(df, detalles, salieron_hoy):
    if df.empty or len(df) < 10:
        return None
    df_ventana = df.tail(VENTANA_SORTEOS)
    nums = df_ventana["numero"].tolist()
    total_v = len(nums)
    conteo_serie = {nombre: 0 for nombre in SERIES.keys()}
    for n in nums:
        for nombre, lista in SERIES.items():
            if n in lista:
                conteo_serie[nombre] += 1
                break
    atraso_serie = {}
    for nombre, lista in SERIES.items():
        posiciones = [i for i, n in enumerate(nums) if n in lista]
        atraso_serie[nombre] = total_v - 1 - posiciones[-1] if posiciones else total_v
    candidatos_serie = []
    for nombre in SERIES.keys():
        freq = conteo_serie[nombre]
        atr = atraso_serie[nombre]
        score_serie = freq * 0.6 + atr * 0.4
        candidatos_serie.append({"nombre": nombre, "freq": freq, "atraso": atr, "score": round(score_serie, 1)})
    candidatos_serie.sort(key=lambda x: x["score"], reverse=True)
    serie_top = candidatos_serie[0]
    lista_serie = SERIES[serie_top["nombre"]]
    candidatos_animales = []
    for num in lista_serie:
        if num in detalles and not detalles[num]["enjaulado"] and num not in salieron_hoy:
            candidatos_animales.append({"num": num, "atraso": detalles[num]["atraso"], "freq_20": detalles[num]["freq_20"]})
    candidatos_animales.sort(key=lambda x: (x["freq_20"], -x["atraso"]), reverse=True)
    if len(candidatos_animales) < 3:
        for num in lista_serie:
            if num in detalles and not detalles[num]["enjaulado"] and num not in [c["num"] for c in candidatos_animales]:
                candidatos_animales.append({"num": num, "atraso": detalles[num]["atraso"], "freq_20": detalles[num]["freq_20"]})
            if len(candidatos_animales) >= 3: break
        candidatos_animales.sort(key=lambda x: (x["freq_20"], -x["atraso"]), reverse=True)
    return {"conteo": conteo_serie, "atraso": atraso_serie, "serie_top": serie_top, "ranking": candidatos_serie, "animales": candidatos_animales[:3]}


def calcular_zona_horaria(df, detalles, salieron_hoy):
    total = len(df)
    nums = df["numero"].tolist()
    if total < 12:
        return []
    ultimos_12 = nums[-12:]
    jales_in = Counter()
    ultimos_3 = nums[-3:]
    for ultimo in ultimos_3:
        for i in range(total - 1):
            if nums[i] == ultimo:
                for j in range(i + 1, min(i + 3, total)):
                    jales_in[nums[j]] += 1
    candidatos = []
    for num in ANIMALITOS_DICT.keys():
        if detalles[num]["atraso"] >= DESCARTE_ATRASO: continue
        if num in salieron_hoy: continue
        atr = detalles[num]["atraso"]
        f12 = ultimos_12.count(num)
        jal = jales_in.get(num, 0)
        score = 0.0
        if 3 <= atr <= 20: score += 0.45
        elif 20 < atr <= 40: score += 0.30
        elif 40 < atr < 60: score += 0.15
        score += min(jal * 0.06, 0.40)
        if f12 >= 2: score += 0.15
        elif f12 == 1: score += 0.05
        candidatos.append({"num": num, "score": round(score * 100, 2), "atraso": atr, "freq_12": f12, "jales": jal})
    candidatos.sort(key=lambda x: x["score"], reverse=True)
    return candidatos[:3]


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
        fv = freq_ventana.get(num, 0); f20 = freq_rec20.get(num, 0); f30 = freq_rec30.get(num, 0)
        atr = atrasos.get(num, 0); atr_hoy = atraso_hoy.get(num, 999); jal = jales_entrantes.get(num, 0)
        n_fv = fv / max_fv if max_fv else 0
        n_f20 = f20 / max_f20 if max_f20 else 0
        n_atr = atr / max_atr if max_atr else 0
        n_jal = jal / max_jal if max_jal else 0
        bonus_caliente = 0.08 if f30 >= 3 else (0.04 if f30 == 2 else 0)
        penal_frio = 0
        if atr > 60: penal_frio = -0.35
        elif atr > 45: penal_frio = -0.20
        elif atr > 30: penal_frio = -0.10
        penal_reciente = 0
        if atr_hoy == 0: penal_reciente = -0.60
        elif atr_hoy == 1: penal_reciente = -0.45
        elif atr_hoy == 2: penal_reciente = -0.30
        elif atr_hoy == 3: penal_reciente = -0.20
        elif atr_hoy == 4: penal_reciente = -0.10
        score = n_fv*0.25 + n_f20*0.25 + n_atr*0.20 + n_jal*0.15 + bonus_caliente + penal_frio + penal_reciente
        if fv == 0: score *= 0.4
        if atr >= DESCARTE_ATRASO: score = 0
        scores[num] = round(max(score, 0) * 100, 2)
        detalles[num] = {"freq_ventana": fv, "freq_20": f20, "atraso": atr, "atraso_hoy": atr_hoy, "jales_in": jal, "caliente": bonus_caliente > 0, "penal": penal_frio < 0, "enjaulado": atr >= DESCARTE_ATRASO}
    top_ordenado = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    alineaciones = detectar_alineaciones(df, min_repeticiones=2)
    ritmos = calcular_ritmo_historico(df)
    return scores, detalles, top_ordenado, jales_aprendidos, alineaciones, fecha_dia_anterior, atrasos, ritmos


def armar_resultados(scores, detalles, top_ordenado, atrasos, salieron_hoy):
    top_validos = [(n, s) for n, s in top_ordenado if not detalles[n]["enjaulado"] and n not in salieron_hoy]
    if len(top_validos) < 3:
        extra = [(n, s) for n, s in top_ordenado if not detalles[n]["enjaulado"] and n not in [x[0] for x in top_validos]]
        top_validos.extend(extra)
    top3 = []
    for num, sc in top_validos[:3]:
        top3.append({"numero": fmt_num(num), "int_num": num, "nombre": ANIMALITOS_DICT[num], "score": sc, "detalle": detalles[num]})
    individual = top3[0] if top3 else None
    nums_oficiales = set([t["int_num"] for t in top3])
    candidatos = [(n, s) for n, s in top_validos if n not in nums_oficiales and s > 0][:20]
    caliente = None
    for n, s in candidatos:
        if detalles[n]["freq_20"] >= 2: caliente = n; break
    if caliente is None and candidatos: caliente = candidatos[0][0]
    maduro = None
    for n, s in candidatos:
        if n == caliente: continue
        atr = atrasos.get(n, 0)
        if 10 <= atr <= 55: maduro = n; break
    if maduro is None:
        for n, s in candidatos:
            if n != caliente: maduro = n; break
    jale = None
    for n, s in candidatos:
        if n in (caliente, maduro): continue
        if detalles[n]["jales_in"] >= 2: jale = n; break
    if jale is None:
        for n, s in candidatos:
            if n not in (caliente, maduro): jale = n; break
    t_alt = [n for n in [caliente, maduro, jale] if n is not None]
    for n, s in candidatos:
        if len(t_alt) >= 3: break
        if n not in t_alt: t_alt.append(n)
    tripleta_alt = []
    for num in t_alt[:3]:
        tripleta_alt.append({"numero": fmt_num(num), "int_num": num, "nombre": ANIMALITOS_DICT[num], "score": scores[num], "detalle": detalles[num]})
    return individual, top3, tripleta_alt


def main():
    st.title("🐾 Granjita Pro")
    st.caption("Tripleta Pensante · Zona Horaria · Series · Filtro 60+")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Leyendo hoja..."):
        df = cargar_historial_google_sheets()

    if df.empty:
        st.error("No se pudieron cargar datos.")
        return

    scores, detalles, top_ordenado, jales_aprendidos, alineaciones, fecha_dia_anterior, atrasos, ritmos = motor_casi_adivino(df)
    if not top_ordenado:
        st.warning("Datos insuficientes.")
        return

    fecha_hoy_str, salieron_hoy = calcular_ultimo_dia(df)
    individual, top3, tripleta_alt = armar_resultados(scores, detalles, top_ordenado, atrasos, salieron_hoy)
    ultimo = df.iloc[-1]

    with st.spinner("Calculando cadenas y tríos..."):
        cadenas = aprender_cadenas(df, max_salto=3)
        trios_hist = buscar_trios_historicos(df, dias_analisis=60, min_repeticiones=2, ventana=11)

    st.caption(f"📅 Día: {fecha_hoy_str} · Ya salieron hoy: {len(salieron_hoy)} animalitos")

    # TRIPLETA PENSANTE
    st.markdown("## 🧠 TRIPLETA PENSANTE")
    st.caption("Combina atraso + cadenas + tríos históricos + series")

    resultado_a = calcular_tripleta_pensante(df, detalles, scores, ritmos, cadenas, trios_hist, salieron_hoy, excluir=None)
    if resultado_a[0]:
        nums_a, exp_a = resultado_a
        st.markdown("### 🎯 TRIPLETA PENSANTE A")
        linea_a = " - ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in nums_a])
        st.success(linea_a)
        st.markdown("**¿Por qué estos 3?**")
        for e in exp_a:
            st.markdown(f"- {e}")
    else:
        st.warning("No se pudo armar la Tripleta Pensante A.")

    st.markdown("")

    excluir_b = set(resultado_a[0]) if resultado_a[0] else set()
    resultado_b = calcular_tripleta_pensante(df, detalles, scores, ritmos, cadenas, trios_hist, salieron_hoy, excluir=excluir_b)
    if resultado_b[0]:
        nums_b, exp_b = resultado_b
        st.markdown("### ⚡ TRIPLETA PENSANTE B (alternativa)")
        linea_b = " - ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in nums_b])
        st.info(linea_b)
        st.markdown("**¿Por qué estos 3?**")
        for e in exp_b:
            st.markdown(f"- {e}")
    else:
        st.warning("No se pudo armar la Tripleta Pensante B.")

    st.markdown("---")

    # ZONA HORARIA
    st.markdown("### ⏰ ZONA HORARIA (próxima hora)")
    zona = calcular_zona_horaria(df, detalles, salieron_hoy)
    if zona:
        for i, z in enumerate(zona, 1):
            st.markdown(f"**#{i} - {fmt_num(z['num'])} {ANIMALITOS_DICT[z['num']]}** — {z['score']}%")
            st.caption(f"Atraso: {z['atraso']} · Freq(12): {z['freq_12']} · Jales: {z['jales']}")
    else:
        st.warning("Sin candidatos válidos.")
    st.markdown("---")

    # SERIE
    st.markdown("### 📊 ANÁLISIS POR SERIE (últimos 60 sorteos)")
    series_info = analizar_series(df, detalles, salieron_hoy)
    if series_info:
        for nombre, freq in series_info["conteo"].items():
            atr = series_info["atraso"][nombre]
            st.write(f"- {nombre}: **{freq}** apariciones · Atraso: {atr}")
        st.markdown(f"### 🎯 SERIE RECOMENDADA: {series_info['serie_top']['nombre']}")
        if series_info["animales"]:
            for a in series_info["animales"]:
                st.write(f"- **{fmt_num(a['num'])} {ANIMALITOS_DICT[a['num']]}** (Atraso: {a['atraso']} · Freq(20): {a['freq_20']})")
    st.markdown("---")

    if alineaciones:
        st.markdown("### 🔗 Alineación Caliente")
        for al in alineaciones[:3]:
            a, b = al["par"]
            if detalles.get(a, {}).get("enjaulado") or detalles.get(b, {}).get("enjaulado"): continue
            if a in salieron_hoy and b in salieron_hoy: continue
            st.markdown(f"**{fmt_num(a)} {ANIMALITOS_DICT[a]} + {fmt_num(b)} {ANIMALITOS_DICT[b]}**")
            st.caption(f"{al['veces']} veces · Promedio cada {al['promedio']} · Atraso: {al['atraso']}")
        st.markdown("---")

    st.markdown("### 🎯 Último resultado")
    st.markdown(f"## {fmt_num(int(ultimo['numero']))} - {ultimo['nombre']}")
    st.caption(f"Fecha: {ultimo['fecha']}")
    st.markdown("---")

    # ANIMALES DE HOY
    fecha_hoy_real = df["fecha"].iloc[-1]
    df_hoy = df[df["fecha"] == fecha_hoy_real].reset_index(drop=True)
    if not df_hoy.empty:
        st.markdown(f"### 📅 Animales de HOY ({fecha_hoy_real}) — Ya salieron {len(df_hoy)}")
        for i, row in df_hoy.iterrows():
            num = int(row["numero"])
            d = detalles.get(num, {})
            st.write(f"{i+1}. **{fmt_num(num)} - {row['nombre']}** (atraso: {d.get('atraso', '?')})")
        st.markdown("---")

    # ANIMALES DE AYER
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
    st.markdown("---")

    st.markdown("### 🔗 Jales Aprendidos")
    ultimo_num = int(ultimo["numero"])
    jales_ult = jales_aprendidos.get(ultimo_num, Counter())
    if jales_ult:
        for jale, c in jales_ult.most_common(3):
            st.write(f"- Después de **{fmt_num(ultimo_num)} {ultimo['nombre']}** → **{fmt_num(jale)} {ANIMALITOS_DICT[jale]}** ({c} veces)")

    with st.expander("📋 Ver últimos 30 sorteos"):
        st.dataframe(df.tail(30)[["fecha", "numero", "nombre"]], use_container_width=True)


if __name__ == "__main__":
    main()
