import streamlit as st
import os
import plotly.graph_objects as go
import re
import math
from fpdf import FPDF
import io

# --- 1. СТИЛИ И ИНТЕРФЕЙС ---
st.set_page_config(page_title="IRON WORKS v10.9", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin: 15px 0; color: #e0f4ff; }
    .ok-card { border-left: 6px solid #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | PDF REPORT ENGINE v10.9</p></div>', unsafe_allow_html=True)

# --- 2. ПАРСЕР ПРАЙСА ---
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

# --- 3. ГЕОМЕТРИЯ 3D ---
def get_clean_box_coords(x0, y0, z0, l, w, h):
    x, y, z = [], [], []
    # Контур основания
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0, z0, z0, z0, z0, None]
    # Контур верха
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0+h, z0+h, z0+h, z0+h, z0+h, None]
    # Стойки
    for dx, dy in [(0,0), (l,0), (l,w), (0,w)]:
        x += [x0+dx, x0+dx, None]; y += [y0+dy, y0+dy, None]; z += [z0, z0+h, None]
    return x, y, z

# --- 4. ФУНКЦИЯ PDF (С ИСПОЛЬЗОВАНИЕМ ТВОЕГО ARIAL.TTF) ---
def generate_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Подключаем твой шрифт arial.ttf
    font_path = "arial.ttf"
    if os.path.exists(font_path):
        pdf.add_font('ArialK', '', font_path)
        pdf.set_font('ArialK', '', 14)
    else:
        pdf.set_font("Helvetica", size=12)

    pdf.cell(200, 10, txt="ОТЧЕТ IRON WORKS: " + report_data['name'], ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('ArialK' if os.path.exists(font_path) else "Helvetica", '', 11)
    for key, value in report_data['metrics'].items():
        pdf.cell(200, 8, txt=f"{key}: {value}", ln=True)
    
    pdf.ln(10)
    pdf.set_font('ArialK' if os.path.exists(font_path) else "Helvetica", 'B', 12)
    pdf.cell(200, 10, txt="ИНЖЕНЕРНОЕ ЗАКЛЮЧЕНИЕ:", ln=True)
    pdf.set_font('ArialK' if os.path.exists(font_path) else "Helvetica", '', 11)
    pdf.multi_cell(0, 8, txt=report_data['advice'])
    
    return pdf.output()

# --- 5. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ВВОД ДАННЫХ")
    if all_prices:
        selected_mat = st.selectbox("ВЫБОР МАТЕРИАЛА:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: ЛИСТ")
            L_s, W_s = st.number_input("Лист Длина", value=2500), st.number_input("Лист Ширина", value=1250)
            L_d, W_d = st.number_input("Деталь Длина", value=600), st.number_input("Деталь Ширина", value=400)
            Qty = st.number_input("Кол-во деталей", value=10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: КАРКАС")
            L_f, W_f, H_f = st.number_input("Длина L", value=2000), st.number_input("Ширина W", value=1000), st.number_input("Высота H", value=1200)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 6. ОСНОВНОЙ БЛОК ---
if calc and all_prices:
    thick = data['thick']
    report_results = {"name": selected_mat, "metrics": {}, "advice": ""}
    
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 0
        paint = (L_s * W_s * 2 / 1_000_000) * needed
        total_w = data['weight'] * needed
        
        report_results["metrics"] = {"Тип": "Листовой металл", "Размер листа": f"{L_s}x{W_s}", "На листе": f"{on_sheet} шт", "Всего листов": f"{needed} шт", "Общий вес": f"{total_w:.1f} кг", "Площадь покраски": f"{paint:.2f} м2"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("На листе", on_sheet); c2.metric("Листов", needed); c3.metric("Вес", f"{total_w:.1f} кг"); c4.metric("Малярка", f"{paint:.2f} м²")
        
        # 3D НЕСТИНГ
        fig = go.Figure()
        xl, yl, zl = get_clean_box_coords(0,0,0, L_s, W_s, thick)
        fig.add_trace(go.Scatter3d(x=xl, y=yl, z=zl, mode='lines', line=dict(color='cyan', width=4), name="Лист"))
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    xd, yd, zd = get_clean_box_coords(c*L_d, r*W_d, thick, L_d, W_d, 2)
                    fig.add_trace(go.Scatter3d(x=xd, y=yd, z=zd, mode='lines', line=dict(color='orange', width=2)))
                    idx += 1
        st.plotly_chart(fig, use_container_width=True)
    else:
        m_real = ((L_f*4)+(W_f*4)+(H_f*4))/1000 * 1.05
        w_total = m_real * data['weight']
        paint = (0.15 * m_real) # Примерная площадь для трубы
        
        report_results["metrics"] = {"Тип": "Профильная труба", "Размеры": f"{L_f}x{W_f}x{H_f}", "Метраж (с зап.)": f"{m_real:.1f} м", "Общий вес": f"{w_total:.1f} кг", "Малярка": f"{paint:.2f} м2"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{w_total:.1f} кг"); c2.metric("Метраж", f"{m_real:.1f} м"); c3.metric("Малярка", f"{paint:.2f} м²"); c4.metric("Смета", f"{(w_total*data['price']*1.1):.0f} грн")
        
        # 3D КАРКАС
        xf, yf, zf = get_clean_box_coords(0,0,0, L_f, W_f, H_f)
        fig = go.Figure(data=go.Scatter3d(x=xf, y=yf, z=zf, mode='lines', line=dict(color='#00c6ff', width=8)))
        st.plotly_chart(fig, use_container_width=True)

    # ИНЖЕНЕРКА
    st.subheader("🛡️ Инженерное заключение")
    is_crit = thick < 2.0
    risk = "ВЫСОКИЙ (Тонкий металл)" if is_crit else "НИЗКИЙ"
    advice = f"Толщина: {thick}мм. Риск деформации: {risk}. Варить: {'прихватками в шахматном порядке' if is_crit else 'сплошным швом, ток 110А'}. Не забывайте проверять диагонали перед сваркой."
    report_results["advice"] = advice
    st.markdown(f'<div class="eng-card {"" if is_crit else "ok-card"}"><b>Инфо:</b> {advice}</div>', unsafe_allow_html=True)

    # ЭКСПОРТ
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Код nanoCAD")
        lisp = f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L_s if is_sheet else L_f} {W_s if is_sheet else W_f} {thick if is_sheet else H_f}) (princ))"
        st.code(lisp, language="lisp")
    with col2:
        st.subheader("📄 Отчет")
        pdf_bytes = generate_pdf(report_results)
        st.download_button("📥 СКАЧАТЬ PDF ОТЧЕТ", data=pdf_bytes, file_name="iron_works_report.pdf", mime="application/pdf")
        