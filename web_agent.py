import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v12.1", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; }
    .crit-high { border-left-color: #ff4b4b; background-color: #2b1b1b; }
    .crit-low { border-left-color: #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | WELDING ENGINEER v12.1</p></div>', unsafe_allow_html=True)

# --- 2. ЛОГИКА СВАРКИ ---
def get_welding_advice(thick):
    if thick < 1.5:
        return {
            "crit": "КРИТИЧЕСКАЯ (Высокий риск прожога)",
            "amp": "30-50A",
            "electrode": "1.6-2.0 мм",
            "method": "Сварка короткими прихватками (точками), обязательное охлаждение.",
            "color": "crit-high"
        }
    elif 1.5 <= thick < 3.0:
        return {
            "crit": "СРЕДНЯЯ (Возможна деформация плоскости)",
            "amp": "60-90A",
            "electrode": "2.5-3.0 мм",
            "method": "Прерывистый шов в шахматном порядке. Контроль диагоналей.",
            "color": ""
        }
    else:
        return {
            "crit": "НИЗКАЯ (Стабильный провар)",
            "amp": "100-140A",
            "electrode": "3.0-4.0 мм",
            "method": "Сплошной шов. При толщине >4мм рекомендуется разделка кромок под 45°.",
            "color": "crit-low"
        }

# --- 3. ПАРСЕР ПРАЙСА ---
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

# --- 4. ГЕОМЕТРИЯ ---
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

# --- 5. PDF ГЕНЕРАТОР ---
def generate_pdf_bytes(report_data, weld):
    pdf = FPDF()
    pdf.add_page()
    f_path = "arial.ttf"
    if os.path.exists(f_path):
        pdf.add_font('Arial', '', f_path)
        pdf.set_font('Arial', '', 14)
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.cell(200, 10, txt=f"ТЕХНИЧЕСКИЙ ОТЧЕТ: {report_data['name']}", ln=True, align='C')
    pdf.ln(5)
    for k, v in report_data['metrics'].items():
        pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
    
    pdf.ln(10)
    pdf.cell(200, 10, txt="ИНЖЕНЕРНО-СВАРОЧНАЯ КАРТА:", ln=True)
    pdf.set_font('Arial' if os.path.exists(f_path) else "Helvetica", '', 10)
    pdf.multi_cell(0, 7, txt=f"Критичность: {weld['crit']}\nРекомендуемый ток: {weld['amp']}\nЭлектрод/Проволока: {weld['electrode']}\nМетод: {weld['method']}")
    
    return bytes(pdf.output())

# --- 6. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        selected_mat = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        st.divider()
        if is_sheet:
            L_s, W_s = st.number_input("Лист L", value=2500), st.number_input("Лист W", value=1250)
            L_d, W_d = st.number_input("Деталь l", value=600), st.number_input("Деталь w", value=400)
            Qty = st.number_input("Кол-во (шт)", value=10, min_value=1)
        else:
            L_f, W_f, H_f = st.number_input("Каркас L", value=2000), st.number_input("Ширина W", value=1000), st.number_input("Высота H", value=1200)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 7. РАСЧЕТ ---
if calc and all_prices:
    thick = data['thick']
    weld = get_welding_advice(thick)
    res = {"name": selected_mat, "metrics": {}, "advice": ""}
    
    if is_sheet:
        on_sheet = (L_s // L_d) * (W_s // W_d)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 1
        w_full = data['weight'] * needed
        res["metrics"] = {"Тип": "Лист", "Толщина": f"{thick} мм", "Вес закупки": f"{w_full:.1f} кг"}
        st.metric("Закупка", f"{w_full:.1f} кг")
    else:
        m_total = (L_f*4 + W_f*4 + H_f*4) / 1000
        w_full = m_total * data['weight']
        res["metrics"] = {"Тип": "Каркас", "Толщина": f"{thick} мм", "Общий метраж": f"{m_total:.2f} м", "Вес изделия": f"{w_full:.1f} кг"}
        st.metric("Вес изделия", f"{w_full:.1f} кг")

    # ИНЖЕНЕРНЫЙ ОТДЕЛ (СВАРКА)
    st.subheader("🛡️ Инженерный отдел: Технология сварки")
    st.markdown(f"""
    <div class="eng-card {weld['color']}">
        <b>Критичность:</b> {weld['crit']}<br>
        <b>Сила тока:</b> {weld['amp']} | <b>Электрод:</b> {weld['electrode']}<br>
        <b>Метод:</b> {weld['method']}
    </div>
    """, unsafe_allow_html=True)

    # 3D ПРЕДОСМОТР
    fig = go.Figure()
    if is_sheet:
        x, y, z = get_clean_box_coords(0,0,0, L_s, W_s, thick)
    else:
        x, y, z = get_clean_box_coords(0,0,0, L_f, W_f, H_f)
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=5)))
    fig.update_layout(scene=dict(aspectmode='data'), height=500)
    st.plotly_chart(fig, use_container_width=True)

    # ЭКСПОРТ
    col1, col2 = st.columns(2)
    with col1:
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L_s if is_sheet else L_f} {W_s if is_sheet else W_f} {thick if is_sheet else H_f}) (princ))", language="lisp")
    with col2:
        pdf_data = generate_pdf_bytes(res, weld)
        st.download_button("📥 СКАЧАТЬ ТЕХ-КАРТУ (PDF)", data=pdf_data, file_name="welding_report.pdf", mime="application/pdf")
        