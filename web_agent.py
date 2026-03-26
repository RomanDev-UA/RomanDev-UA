import streamlit as st
import pandas as pd
import re
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# --- 1. НАСТРОЙКИ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="RomanDev IronWorks", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .main-title {
        font-size: 45px;
        font-weight: 800;
        background: -webkit-linear-gradient(#00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-bottom: 20px;
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stMetricValue"] {
        font-size: 32px;
        color: #00c6ff;
    }
    .stButton>button {
        border-radius: 20px;
        background: linear-gradient(45deg, #0072ff, #00c6ff);
        color: white;
        border: none;
        height: 60px;
        font-weight: bold;
        font-size: 20px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,198,255,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🛠️ ROMAN_DEV | IRON WORKS v8.0</p>', unsafe_allow_html=True)

# --- 2. ЗАГРУЗКА ДАННЫХ ---
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

all_prices = load_prices()

# --- 3. БОКОВАЯ ПАНЕЛЬ (ВВОД ДАННЫХ) ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    
    if all_prices:
        display_options = {n: f"🔹 {n}" for n in all_prices.keys()}
        sel_disp = st.selectbox("МАТЕРИАЛ:", options=list(display_options.values()))
        found_name = [n for n, d in display_options.items() if d == sel_disp][0]
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name
        
        st.divider()
        if is_sheet:
            L_d = st.number_input("Длина детали (мм)", min_value=1, value=500)
            W_d = st.number_input("Ширина детали (мм)", min_value=1, value=300)
            Qty = st.number_input("Количество (шт)", min_value=1, value=10)
        else:
            L_f = st.number_input("Длина L (мм)", min_value=1, value=2000, step=10)
            W_f = st.number_input("Ширина W (мм)", min_value=1, value=1500, step=10)
            H_f = st.number_input("Высота H (мм)", min_value=1, value=1000, step=10)
    else:
        st.error("Файл prices.txt не найден!")
        found_name = None

    st.divider()
    calc = st.button("🔥 ЗАПУСТИТЬ РАСЧЕТ", use_container_width=True)

# --- 4. ОСНОВНОЙ ЭКРАН (РАСЧЕТЫ И ГРАФИКА) ---
if calc and found_name:
    st.subheader(f"📊 Аналитика для: {found_name}")
    
    if not is_sheet:
        # 1. ЧИСТЫЙ РАСЧЕТ
        pure_len_m = ((L_f * 4) + (W_f * 4) + (H_f * 4)) / 1000
        
        # 2. УЧЕТ ОСТАТКОВ И РЕЗА (+5%)
        total_len_m = pure_len_m * 1.05
        
        # 3. ВЕС И ЦЕНА (с учетом "перегрева" бюджета на расходники +10%)
        weight_total = total_len_m * sel['weight']
        # Добавляем 10% к цене на электроды/диски/краску
        cost_total = (weight_total * sel['price']) * 1.10
        
        # ВЫВОД МЕТРИК
        col1, col2, col3 = st.columns(3)
        col1.metric("Вес (+5% запас)", f"{weight_total:.2f} кг")
        col2.metric("Длина с обрезом", f"{total_len_m:.2f} м")
        col3.metric("Итого (с расходниками)", f"{cost_total:.0f} грн")

        # В отчет (report_text) тоже добавим эти данные:
        report_text = f"""ОТЧЕТ: ROMAN_DEV IRON WORKS
-------------------------------------------
Материал: {found_name}
Габариты: {L_f}x{W_f}x{H_f} мм

ДЕТАЛИЗАЦИЯ (Чистый размер):
- Стойки: 4 шт x {H_f} мм
- Прогоны: 4 шт x {L_f} мм
- Поперечины: 4 шт x {W_f} мм

ЭКОНОМИКА (С учетом запаса 5% и расходников 10%):
- Общая длина закупки: {total_len_m:.2f} м
- Расчетный вес: {weight_total:.2f} кг
- Итоговая сумма: {cost_total:.0f} грн
-------------------------------------------
"""
        

        # --- 3D ВИЗУАЛИЗАЦИЯ ---
        st.markdown("### 🏗️ 3D Визуализация каркаса")
        fig = plt.figure(figsize=(10, 7))
        # Фикс для темной темы
        fig.patch.set_facecolor('#0e1117')
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#0e1117')
        
        # Ребра параллелепипеда
        edges = [
            ([0, L_f], [0, 0], [0, 0]), ([0, L_f], [W_f, W_f], [0, 0]),
            ([0, L_f], [0, 0], [H_f, H_f]), ([0, L_f], [W_f, W_f], [H_f, H_f]),
            ([0, 0], [0, W_f], [0, 0]), ([L_f, L_f], [0, W_f], [0, 0]),
            ([0, 0], [0, W_f], [H_f, H_f]), ([L_f, L_f], [0, W_f], [H_f, H_f]),
            ([0, 0], [0, 0], [0, H_f]), ([L_f, L_f], [0, 0], [0, H_f]),
            ([0, 0], [W_f, W_f], [0, H_f]), ([L_f, L_f], [W_f, W_f], [0, H_f])
        ]
        
        for x, y, z in edges:
            ax.plot(x, y, z, color='#00c6ff', linewidth=3, marker='o')

        ax.grid(False)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.zaxis.label.set_color('white')
        ax.tick_params(axis='x', colors='gray')
        ax.tick_params(axis='y', colors='gray')
        ax.tick_params(axis='z', colors='gray')
        
        st.pyplot(fig)
        # --- 5. ДЕТАЛИЗАЦИЯ И СКАЧИВАНИЕ ---
        st.markdown("### 📋 Спецификация на резку")
        
        # Формируем таблицу деталей
        df_cut = pd.DataFrame({
            "Наименование": [f"Стойки (H)", f"Прогоны (L)", f"Поперечины (W)"],
            "Кол-во (шт)": [4, 4, 4],
            "Длина (мм)": [H_f, L_f, W_f],
            "Итого (м)": [(H_f*4)/1000, (L_f*4)/1000, (W_f*4)/1000]
        })
        st.table(df_cut)

        # Формируем текст для скачивания
        report_text = f"""ОТЧЕТ ПО РАСЧЕТУ: ROMAN_DEV IRON WORKS
-------------------------------------------
Материал: {found_name}
Габариты каркаса: {L_f}x{W_f}x{H_f} мм

ДЕТАЛИЗАЦИЯ ДЛЯ РЕЗКИ:
1. Стойки (Высота H): 4 шт x {H_f} мм
2. Прогоны (Длина L): 4 шт x {L_f} мм
3. Поперечины (Ширина W): 4 шт x {W_f} мм

ИТОГО:
- Общая длина проката: {total_len_m:.2f} м
- Общий вес: {weight_total:.2f} кг
- Ориентировочная стоимость: {cost_total:.0f} грн
-------------------------------------------
Дата расчета: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
"""

        # КНОПКА СКАЧИВАНИЯ
        st.download_button(
            label="📥 СКАЧАТЬ РЕЗУЛЬТАТ (.TXT)",
            data=report_text,
            file_name=f"Calculation_{L_f}x{W_f}x{H_f}.txt",
            mime="text/plain",
            use_container_width=True
        )

    else:
        st.success(f"Расчет для листов выполнен! Вес: {(L_d*W_d*Qty/1000000)*sel['weight']:.2f} кг")
        st.info("3D модель для листов будет добавлена в v8.1")
