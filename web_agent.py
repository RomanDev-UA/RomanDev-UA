import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ ---
st.set_page_config(page_title="IRON WORKS v12.0", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .waste-card { background-color: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | WASTE CONTROL v12.0</p></div>', unsafe_allow_html=True)

# --- 2. ПАРСЕР ---
@st.cache_data
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line: continue
                try:
                    clean_line = re.sub(r'^\d+:\s*', '', line)
                    parts = clean_line.split(",")
                    name = ",".join(parts[:-2]).strip()
                    weight = float(parts[-2].replace(",", "."))
                    price = float(parts[-1].replace(",", "."))
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    prices[name] = {"weight": weight, "price": price, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ГЕОМЕТРИЯ ---
def get_clean_box_coords(x0, y0, z0, l, w, h):
    x, y, z = [], [], []
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0, z0, z0, z0, z0, None]
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0+h, z0+h, z0+h, z0+h, z0+h, None]
    for dx, dy in [(0,0), (l,0), (l,w), (0,w)]:
        x += [x0+dx, x0+dx, None]; y += [y0+dy, y0+dy, None]; z += [z0, z0+h, None]
    return x, y, z

# --- 4. PDF ГЕНЕРАТОР ---
def generate_pdf_bytes(report_data):
    pdf = FPDF()
    pdf.add_page()
    font_path = "arial.ttf"
    f_name = "ArialCustom"
    if os.path.exists(font_path):
        pdf.add_font(f_name, '', font_path)
        pdf.set_font(f_name, '', 14)
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.cell(200, 10, txt=f"ОТЧЕТ IRON WORKS: {report_data['name']}", ln=True, align='C')
    pdf.ln(5)
    for key, value in report_data['metrics'].items():
        pdf.cell(200, 8, txt=f"{key}: {value}", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 8, txt=f"ЗАКЛЮЧЕНИЕ:\n{report_data['advice']}")
    return bytes(pdf.output())

# --- 5. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        selected_mat = st.selectbox("ВЫБОР МАТЕРИАЛА:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        st.divider()
        if is_sheet:
            L_s, W_s = st.number_input("Лист L (мм)", value=2500), st.number_input("Лист W (мм)", value=1250)
            L_d, W_d = st.number_input("Деталь l (мм)", value=600), st.number_input("Деталь w (мм)", value=400)
            Qty = st.number_input("Кол-во (шт)", value=10, min_value=1)
        else:
            L_f, W_f, H_f = st.number_input("Каркас L (мм)", value=2000), st.number_input("Ширина W (мм)", value=1000), st.number_input("Высота H (мм)", value=1200)
            stock_len = st.number_input("Длина целой трубы (м)", value=6.0)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 6. РАСЧЕТ И ЛОГИКА ---
if calc and all_prices:
    thick = data['thick']
    report_results = {"name": selected_mat, "metrics": {}, "advice": ""}
    
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed_sheets = -(-Qty // on_sheet) if on_sheet > 0 else 1
        
        # РАСЧЕТ ОТХОДОВ (ЛИСТ)
        area_total = (L_s * W_s * needed_sheets) / 1_000_000
        area_useful = (L_d * W_d * Qty) / 1_000_000
        waste_percent = ((area_total - area_useful) / area_total) * 100
        weight_full = data['weight'] * needed_sheets
        weight_useful = (weight_full / area_total) * area_useful
        
        report_results["metrics"] = {
            "Тип": "Листовой металл",
            "Всего листов": f"{needed_sheets} шт",
            "Чистый вес изделий": f"{weight_useful:.1f} кг",
            "Вес закупки (с отходом)": f"{weight_full:.1f} кг",
            "Процент отхода": f"{waste_percent:.1f}%"
        }
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{weight_full:.1f} кг")
        c2.metric("Чистый вес", f"{weight_useful:.1f} кг")
        c3.metric("Отход", f"{waste_percent:.1f}%", delta=f"{weight_full-weight_useful:.1f} кг", delta_color="inverse")
        c4.metric("Малярка", f"{(area_useful*2):.2f} м²")

        fig = go.Figure()
        xl, yl, zl = get_clean_box_coords(0,0,0, L_s, W_s, thick)
        fig.add_trace(go.Scatter3d(x=xl, y=yl, z=zl, mode='lines', line=dict(color='cyan', width=4)))
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    xd, yd, zd = get_clean_box_coords(c*L_d, r*W_d, thick, L_d, W_d, 1)
                    fig.add_trace(go.Scatter3d(x=xd, y=yd, z=zd, mode='lines', line=dict(color='orange', width=2)))
                    idx += 1
        fig.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig, use_container_width=True)

    else:
        # РАСЧЕТ ОТХОДОВ (ТРУБА)
        total_len_mm = (L_f*4 + W_f*4 + H_f*4)
        total_len_m = total_len_mm / 1000
        needed_sticks = -(-total_len_m // stock_len)
        weight_full = needed_sticks * stock_len * data['weight']
        weight_useful = total_len_m * data['weight']
        waste_m = (needed_sticks * stock_len) - total_len_m
        waste_percent = (waste_m / (needed_sticks * stock_len)) * 100
        
        report_results["metrics"] = {
            "Тип": "Профильная труба",
            "Кол-во целых палок": f"{needed_sticks} шт по {stock_len}м",
            "Чистый метраж": f"{total_len_m:.2f} м",
            "Вес закупки": f"{weight_full:.1f} кг",
            "Обрезки (лом)": f"{waste_m:.2f} м ({waste_percent:.1f}%)"
        }
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес закупки", f"{weight_full:.1f} кг")
        c2.metric("Чистый вес", f"{weight_useful:.1f} кг")
        c3.metric("Отход", f"{waste_percent:.1f}%", delta=f"{waste_m:.1f} м", delta_color="inverse")
        c4.metric("Смета (+10%)", f"{(weight_full * data['price'] * 1.1):.0f} грн")

        xf, yf, zf = get_clean_box_coords(0,0,0, L_f, W_f, H_f)
        fig = go.Figure(data=go.Scatter3d(x=xf, y=yf, z=zf, mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), height=600)
        st.plotly_chart(fig, use_container_width=True)

    # ВЫВОД ПРЕДУПРЕЖДЕНИЯ ОБ ОТХОДАХ
    if waste_percent > 20:
        st.markdown(f'<div class="waste-card">⚠️ <b>ВНИМАНИЕ:</b> Высокий уровень отхода ({waste_percent:.1f}%). Попробуйте изменить раскладку или выбрать другой формат сырья.</div>', unsafe_allow_html=True)

    # ИНЖЕНЕРКА
    advice = f"Материал {thick}мм. При расчете учтен технологический запас на резку и торцовку. Чистый вес изделия: {weight_useful:.1f} кг."
    report_results["advice"] = advice
    st.markdown(f'<div class="eng-card"><b>Инженерный отдел:</b> {advice}</div>', unsafe_allow_html=True)

    # ЭКСПОРТ
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L_s if is_sheet else L_f} {W_s if is_sheet else W_f} {thick if is_sheet else H_f}) (princ))", language="lisp")
    with col2:
        pdf_data = generate_pdf_bytes(report_results)
        st.download_button("📥 СКАЧАТЬ ПОЛНЫЙ ОТЧЕТ", data=pdf_data, file_name="iron_waste_report.pdf", mime="application/pdf")
        