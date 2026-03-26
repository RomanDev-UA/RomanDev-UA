import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- 1. НАСТРОЙКИ И СТИЛИ (ОСТАЕМСЯ В ТЕМЕ) ---
st.set_page_config(page_title="RomanDev IronWorks", layout="wide")
st.markdown("""
    <style>
    .main-title { font-size: 45px; font-weight: 800; background: -webkit-linear-gradient(#00c6ff, #0072ff);
                  -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 15px; border: 1px solid #3e445b; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🛠️ ROMAN_DEV | IRON WORKS v8.2</p>', unsafe_allow_html=True)

# --- 2. ЗАГРУЗКА ЦЕН ---
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    parts = line.strip().split(",")
                    name = ",".join(parts[:-2]).strip()
                    prices[name] = {"weight": float(parts[-2]), "price": float(parts[-1])}
    return prices

all_prices = load_prices()

# --- 3. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ НАСТРОЙКИ")
    if all_prices:
        found_name = st.selectbox("ВЫБЕРИТЕ МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name or "Лист" in found_name.capitalize()
        
        st.divider()
        if is_sheet:
            st.info("📦 РЕЖИМ: РАСКРОЙ ЛИСТА")
            L_d = st.number_input("Длина детали (мм)", min_value=1, value=1000)
            W_d = st.number_input("Ширина детали (мм)", min_value=1, value=500)
            Qty = st.number_input("Количество деталей (шт)", min_value=1, value=1)
        else:
            st.info("🏗️ РЕЖИМ: КАРКАС / ПРОКАТ")
            L_f = st.number_input("Длина L (мм)", min_value=1, value=2000)
            W_f = st.number_input("Ширина W (мм)", min_value=1, value=1500)
            H_f = st.number_input("Высота H (мм)", min_value=1, value=1000)
            
        st.divider()
        calc = st.button("🚀 ЗАПУСТИТЬ ПОЛНЫЙ РАСЧЕТ", use_container_width=True)
    else:
        st.error("Файл prices.txt не найден!")

# --- 4. ЛОГИКА ВЫВОДА ---
if calc and all_prices:
    if is_sheet:
        # --- РАСЧЕТ ДЛЯ ЛИСТА ---
        area_one = (L_d * W_d) / 1_000_000  # м2 одной детали
        total_area = area_one * Qty * 1.05  # +5% запас
        weight_total = total_area * sel['weight']
        cost_total = (weight_total * sel['price']) * 1.10 # +10% расходники
        cutting_path = ((L_d + W_d) * 2 * Qty) / 1000 # погонные метры реза

        col1, col2, col3 = st.columns(3)
        col1.metric("Общий вес (кг)", f"{weight_total:.2f}")
        col2.metric("Площадь (+5%)", f"{total_area:.2f} м²")
        col3.metric("Цена (с зач. дисками)", f"{cost_total:.0f} грн")
        
        st.write(f"✂️ **Длина реза:** {cutting_path:.1f} м.п. (учтите при выборе дисков/газа)")
        
        report_text = f"ЛИСТ: {found_name}\nДетали: {L_d}x{W_d} мм ({Qty} шт)\nВес: {weight_total:.2f} кг\nЦена: {cost_total:.0f} грн"

    else:
        # --- РАСЧЕТ ДЛЯ КАРКАСА (ТВОЙ ЛЮБИМЫЙ 3D) ---
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        total_len = pure_len * 1.05
        weight_total = total_len * sel['weight']
        cost_total = (weight_total * sel['price']) * 1.10
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Вес (кг)", f"{weight_total:.2f}")
        col2.metric("Метраж (м)", f"{total_len:.2f}")
        col3.metric("Цена (грн)", f"{cost_total:.0f}")

        # РИСУЕМ 3D
        fig = plt.figure(figsize=(8, 5))
        ax = fig.add_subplot(111, projection='3d')
        # (код отрисовки каркаса...)
        st.pyplot(fig)
        
        report_text = f"КАРКАС: {found_name}\nРазмеры: {L_f}x{W_f}x{H_f}\nВес: {weight_total:.2f} кг"

    st.download_button("📥 СКАЧАТЬ ТХТ ОТЧЕТ", report_text, file_name="iron_works_report.txt")
    