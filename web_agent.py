import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ И КРАСИВЫЙ ЗАГОЛОВОК ---
st.set_page_config(page_title="IRON WORKS v13.8", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Full Engineering v13.8</h1></div>', unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF (Локальный шрифт) ---
def create_pdf(res, weld_info):
    pdf = FPDF()
    pdf.add_page()
    font_file = "arial.ttf"
    if os.path.exists(font_file):
        pdf.add_font("CustomFont", "", font_file)
        pdf.set_font("CustomFont", "", 14)
    else:
        pdf.set_font("Arial", "B", 14)
    
    pdf.cell(200, 10, txt="ТЕХНИЧЕСКАЯ СМЕТА - IRON WORKS", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial" if not os.path.exists(font_file) else "CustomFont", "", 12)
    pdf.cell(200, 10, txt=f"Материал: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Вес: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Отход: {res['waste']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО: {res['total']:.0f} грн", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Техпроцесс: {weld_info['meth']}")
    return pdf.output()

# --- 3. ПАРСЕР И ТЕХНОЛОГИЯ ---
@st.cache_data
def load_db():
    catalog = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line: continue
                try:
                    clean_line = re.sub(r'^\d+:\s*', '', line)
                    parts = clean_line.split(",")
                    name = parts[0].strip()
                    weight = float(parts[1].strip().replace(',', '.'))
                    p_unit = float(parts[2].strip().replace(',', '.'))
                    p_ton = float(parts[3].strip().replace(',', '.'))
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    catalog[name] = {"weight": weight, "p_unit": p_unit, "p_ton": p_ton, "thick": thick}
                except: continue
    return catalog

db = load_db()

def get_welding_advice(thick):
    if thick < 2.0: return {"crit": "ВЫСОКАЯ (Тонкий металл)", "amp": "40-60A", "meth": "Сварка короткими прихватками, чтобы не повело."}
    return {"crit": "НОРМАЛЬНАЯ", "amp": "90-120A", "meth": "Сплошной шов, контроль глубины провара."}

# --- 4. ИНТЕРФЕЙС ---
if db:
    with st.sidebar:
        st.header("⚙️ Настройки")
        sel = st.selectbox("Материал:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Тип цены:", ["Розница", "Опт (Тонна)"])
        
        if is_sheet:
            L, W = st.number_input("Лист L", 2500.0), st.number_input("Лист W", 1250.0)
            dl, dw = st.number_input("Деталь L", 600.0), st.number_input("Деталь W", 400.0)
            qty = st.number_input("Кол-во шт", 1, 1000, 10)
        else:
            rl, rw, rh = st.number_input("Габарит L (мм)", 2000.0), st.number_input("W (мм)", 1000.0), st.number_input("H (мм)", 1200.0)
            stock = st.number_input("Палка (м)", 6.0)
            
        markup = st.slider("Наценка %", 0, 100, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        weld = get_welding_advice(item['thick'])
        
        # ЛОГИКА РАСЧЕТА
        if is_sheet:
            on_sheet = max(1, (L // dl) * (W // dw))
            count_val = -(-qty // on_sheet)
            weight_buy = count_val * item['weight']
            base = (count_val * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((count_val * L * W - qty * dl * dw) / (count_val * L * W)) * 100
        else:
            m_total = (rl*4 + rw*4 + rh*4) / 1000
            count_val = -(-m_total // max(0.1, stock))
            weight_buy = count_val * stock * item['weight']
            base = (count_val * stock * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((count_val * stock - m_total) / (count_val * stock)) * 100

        total_price = base * (1 + markup/100)

        # ВЫВОД МЕТРИК
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(count_val)} {'л.' if is_sheet else 'п.'}")
        c2.metric("Вес", f"{weight_buy:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # ИНЖЕНЕРНЫЙ БЛОК
        st.subheader("🛠️ Инженерный анализ")
        st.markdown(f'<div class="eng-card"><b>СЛОЖНОСТЬ:</b> {weld["crit"]}<br><b>ТОК:</b> {weld["amp"]}<br><b>МЕТОД:</b> {weld["meth"]}</div>', unsafe_allow_html=True)
        
        if waste > 20:
            st.markdown(f'<div class="waste-card">⚠️ Высокий отход металла ({waste:.1f}%)!</div>', unsafe_allow_html=True)

        # --- ВОЗВРАТ 3D-МОДЕЛИ ---
        st.subheader("📦 3D Визуализация каркаса")
        fig = go.Figure()
        
        # Координаты для 3D бокса
        lx, ly, lz = (L if is_sheet else rl), (W if is_sheet else rw), (item['thick'] if is_sheet else rh)
        
        x = [0, lx, lx, 0, 0,  0, lx, lx, 0, 0, None, lx, lx, None, 0, 0, None, lx, lx, None, 0, 0]
        y = [0, 0, ly, ly, 0,  0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly, None, 0, 0]
        z = [0, 0, 0, 0, 0,  lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz, None, 0, lz]
        
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=5)))
        fig.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0), paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

        # КНОПКА PDF
        st.divider()
        res_data = {"name": sel, "weight": weight_buy, "waste": waste, "total": total_price}
        pdf_bytes = create_pdf(res_data, weld)
        st.download_button(label="📥 СКАЧАТЬ СМЕТУ PDF", data=pdf_bytes, file_name="IronWorks_Smeta.pdf", mime="application/pdf", use_container_width=True)

st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L if is_sheet else rl} {W if is_sheet else rw} {item['thick'] if is_sheet else rh}) (princ))")
