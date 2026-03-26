import streamlit as st
import re
import os
from datetime import datetime
# Твои рабочие модули
from modules.optimizer import optimize_cutting
from modules.renderer import generate_3d_model
from modules.pdf_report import create_pdf_report

def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    k, data = line.strip().split(":")
                    name, w, p = data.split(",")
                    prices[name] = {"weight": float(w), "price": float(p)}
    return prices

# Настройка страницы
st.set_page_config(page_title="RomanDev Engineering Web", layout="centered")
st.title("🏗️ RomanDev Engineering Suite v6.0")
st.write("Веб-интерфейс для расчета металлоконструкций")

prices = load_prices()

# Боковая панель ввода
st.sidebar.header("Параметры каркаса")
L = st.sidebar.number_input("Длина (L), мм", value=2000)
W = st.sidebar.number_input("Ширина (W), мм", value=1500)
H = st.sidebar.number_input("Высота (H), мм", value=1000)

mat_name = st.selectbox("Выберите материал из прайса:", list(prices.keys()))

if st.button("🚀 РАССЧИТАТЬ ПРОЕКТ"):
    sel = prices[mat_name]
    
    # Расчет деталей
    details = [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Перемычка L", "qty": 4, "size": L},
        {"item": "Перемычка W", "qty": 4, "size": W}
    ]
    all_pieces = [d['size'] for d in details for _ in range(int(d['qty']))]
    
    # Логика труб/листов
    bins = []
    if "Труба" in mat_name:
        bins = optimize_cutting(all_pieces, 6000, kerf=3)
        total_len = len(bins) * 6
    else:
        total_len = (L * W * 2) / 1000 # Упрощенно для листов
        
    total_cost = total_len * sel['price']
    total_weight = total_len * sel['weight']
    
    # Физика сварки
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", mat_name)
    wall = float(nums[-1]) if nums else 2.0
    if wall <= 1.5: advice = "КРИТИЧЕСКИЙ НАГРЕВ! Варить прихватками."
    elif wall <= 3.0: advice = "УМЕРЕННЫЙ РИСК. Стандартный ток."
    else: advice = "НИЗКИЙ РИСК. Можно варить сплошным швом."

    # Вывод результатов на экран
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Общий вес", f"{total_weight:.1f} кг")
        st.metric("Стоимость", f"{total_cost:.0f} грн")
    with col2:
        st.info(f"**Совет инженера:**\n{advice}")

    # Генерация файлов
    generate_3d_model(L, W, H, details)
    pdf_file = create_pdf_report(L, W, H, mat_name, total_cost, total_weight, bins, advice, 5.0)

    # Кнопка скачивания PDF
    with open(pdf_file, "rb") as f:
        st.download_button("📥 СКАЧАТЬ PDF ОТЧЕТ", f, file_name="Order_Report.pdf")

    st.success("✅ Расчет завершен! 3D-модель обновлена.")
    