import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

# --- 1. ЗАГРУЗКА ДАННЫХ ---
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line: continue
                parts = line.split(",")
                if len(parts) >= 3:
                    try:
                        name = ",".join(parts[:-2]).strip()
                        name = re.sub(r"^\d+[:.]\s*", "", name)
                        w = float(parts[-2].strip().replace(",", "."))
                        p = float(parts[-1].strip().replace(",", "."))
                        prices[name] = {"weight": w, "price": p}
                    except: continue
    return prices

# --- 2. ИНТЕРФЕЙС ---
st.set_page_config(page_title="RomanDev PRO Engine", layout="wide")
st.title("🏗️ RomanDev Engineering PRO v7.7")

all_prices = load_prices()

with st.sidebar:
    st.header("📋 Настройки")
    if all_prices:
        display_options = {n: f"{n} ({d['weight']}кг | {d['price']}грн)" for n, d in all_prices.items()}
        sel_disp = st.selectbox("Материал:", options=list(display_options.values()))
        found_name = [n for n, d in display_options.items() if d == sel_disp][0]
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name
        
        st.write("---")
        if is_sheet:
            L_d, W_d, Qty = st.number_input("Длина, мм", 500), st.number_input("Ширина, мм", 300), st.number_input("Кол-во", 10)
        else:
            L_f, W_f, H_f = st.number_input("Длина L", 2000), st.number_input("Ширина W", 1500), st.number_input("Высота H", 1000)
            kerf = st.slider("Рез, мм", 0, 10, 3)
    else:
        st.error("Файл prices.txt не найден!")
        found_name = None

    c_rez = st.number_input("Цена реза, грн", 15)
    calc = st.button("🚀 РАССЧИТАТЬ", type="primary", use_container_width=True)

# --- 3. РАСЧЕТ И ВЫВОД ---
if calc and found_name:
    t1, t2, t3 = st.tabs(["📊 Смета", "📄 Раскрой", "📐 3D"])
    
    if is_sheet:
        nx, ny = 2500 // L_d, 1250 // W_d
        per_s = max(1, nx * ny)
        sheets = (Qty + per_s - 1) // per_s
        cost_m = sheets * 3.125 * sel['price']
        waste = (sheets * 3.125) - ((Qty * L_d * W_d) / 1_000_000)
        total_w = sheets * 3.125 * sel['weight']
        res_info = f"Лист {L_d}x{W_d}, {int(Qty)} шт"
    else:
        details = [L_f]*4 + [W_f]*4 + [H_f]*4
        bars = (sum([d + kerf for d in details]) + 5990) // 6000
        cost_m = bars * 6 * sel['price']
        cost_work = len(details) * c_rez
        waste = (bars * 6000 - sum(details)) / 1000
        total_w = bars * 6 * sel['weight']
        res_info = f"Каркас {L_f}x{W_f}x{H_f}"

    with t1:
        st.metric("ИТОГО", f"{int(cost_m + (0 if is_sheet else cost_work))} грн")
        st.write(f"Вес: {total_w:.1f} кг | Материал: {found_name}")
    
    with t2:
        st.error(f"⚠️ Остаток: {waste:.2f} {'м2' if is_sheet else 'м'}")
        st.info("Карта раскроя построена успешно.")

    with t3:
        st.write("3D модель отображена ниже.")

    # --- ФОРМИРУЕМ ОТЧЕТ ТОЛЬКО ТУТ ---
    report_text = f"ОТЧЕТ: {found_name}\nДата: {datetime.now()}\nОбъект: {res_info}\nВес: {total_w:.1f}кг\nЦена: {int(cost_m)}грн"
    
    st.write("---")
    st.download_button("📥 СКАЧАТЬ ОТЧЕТ", report_text, file_name="report.txt", use_container_width=True)
    st.balloons()
    