import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ СТИЛЕЙ ---
st.set_page_config(page_title="IRON WORKS v13.5", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .price-details { background: #1b2b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; color: #ccffea; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

# КРАСИВЫЙ ЗАГОЛОВОК
st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Full Engineering v13.5</h1><p style="color: #00c6ff; font-size: 18px; margin: 0;">Профессиональный расчет и техпроцесс сварки</p></div>', unsafe_allow_html=True)

# --- 2. ФУНКЦИЯ PDF ---
def create_pdf(res, weld_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt="IRON WORKS - ТЕХНИЧЕСКАЯ СМЕТА", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, txt=f"Материал: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Вес закупки: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Отход: {res['waste']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО К ОПЛАТЕ: {res['total']:.0f} грн", ln=True)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, txt="ИНЖЕНЕРНЫЕ ПАРАМЕТРЫ СВАРКИ:", ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, txt=f"Ток: {weld_info['amp']}\nМетод: {weld_info['meth']}")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. ПАРСЕР И ЛОГИКА ---
@st.cache_data
def load_db():
    catalog = {}
    if not os.path.exists("prices.txt"): return catalog
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
    if thick < 1.6:
        return {"crit": "ВЫСОКАЯ (Риск прожога)", "amp": "30-55A", "el": "1.6-2.0мм", "meth": "Точечно, с паузами. Контроль деформаций."}
    elif 1.6 <= thick < 3.0:
        return {"crit": "СРЕДНЯЯ", "amp": "65-95A", "el": "2.5-3.0мм", "meth": "Прерывистый шов для минимизации потяжек."}
    else:
        return {"crit": "НИЗКАЯ", "amp": "100-145A", "el": "3.0-4.0мм", "meth": "Сплошной шов. Свыше 4мм — разделка кромок."}

# --- 4. ИНТЕРФЕЙС ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Металлопрокат:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Расценка:", ["Розница (м.п./шт)", "Опт (Тонна)"])
        
        if is_sheet:
            L, W = st.number_input("Лист L", 2500.0), st.number_input("Лист W", 1250.0)
            dl, dw = st.number_input("Деталь l", 600.0), st.number_input("Деталь w", 400.0)
            qty = st.number_input("Кол-во шт", 1, 1000, 10)
        else:
            rl, rw, rh = st.number_input("Длина (мм)", 2000.0), st.number_input("Ширина (мм)", 1000.0), st.number_input("Высота (мм)", 1200.0)
            stock = st.number_input("Палка (м)", 6.0)
            
        markup = st.slider("Наценка %", 0, 100, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        weld = get_welding_advice(item['thick'])
        
        if is_sheet:
            on_sheet = max(1, (L // dl) * (W // dw))
            count_val = -(-qty // on_sheet)
            weight_buy = count_val * item['weight']
            base = (count_val * item['p_unit']) if "Розница" in mode else (weight_buy/1000 * item['p_ton'])
            waste = ((count_val * L * W - qty * dl * dw) / (count_val * L * W)) * 100
            unit_label = "листов"
        else:
            m_clear = (rl*4 + rw*4 + rh*4) / 1000
            count_val = -(-m_clear // max(0.1, stock))
            weight_buy = count_val * stock * item['weight']
            base = (count_val * stock * item['p_unit']) if "Розница" in mode else (weight_buy/1000 * item['p_ton'])
            waste = ((count_val * stock - m_clear) / (count_val * stock)) * 100
            unit_label = "палок"

        total_price = base * (1 + markup/100)

        # МЕТРИКИ
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(count_val)} {unit_label}")
        c2.metric("Вес", f"{weight_buy:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # ПОДСКАЗКИ
        st.markdown(f'<div class="price-details">💰 Металл: {base:.2f} грн | Наценка: {markup}% | Итого: <b>{total_price:.2f} грн</b></div>', unsafe_allow_html=True)
        
        st.subheader("🛠️ Инженерный отдел")
        st.markdown(f"""<div class="eng-card"><b>СЛОЖНОСТЬ:</b> {weld['crit']}<br><b>ТОК:</b> {weld['amp']} | <b>ЭЛЕКТРОД:</b> {weld['el']}<br><b>МЕТОД:</b> {weld['meth']}</div>""", unsafe_allow_html=True)
        
        if waste > 20:
            st.markdown(f'<div class="waste-card">⚠️ Высокий отход: {waste:.1f}%! Проверьте размеры.</div>', unsafe_allow_html=True)

        # 3D МОДЕЛЬ
        fig = go.Figure(data=[go.Scatter3d(x=[0, rl if not is_sheet else L], y=[0, rw if not is_sheet else W], z=[0, rh if not is_sheet else 2], mode='lines', line=dict(color='#00c6ff', width=8))])
        fig.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0), paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

        # КНОПКА PDF В САМОМ НИЗУ
        st.divider()
        pdf_res = {"name": sel, "weight": weight_buy, "waste": waste, "total": total_price}
        pdf_bytes = create_pdf(pdf_res, weld)
        st.download_button(label="📥 СКАЧАТЬ СМЕТУ (PDF)", data=pdf_bytes, file_name=f"Smeta_{sel}.pdf", mime="application/pdf", use_container_width=True)

st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L if is_sheet else rl} {W if is_sheet else rw} {item['thick'] if is_sheet else rh}) (princ))")
