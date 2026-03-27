import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ И ИНТЕРФЕЙС ---
st.set_page_config(page_title="IRON WORKS v14.4", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Cutting & Engineering v14.4</h1></div>', unsafe_allow_html=True)

# --- 2. ФУНКЦИЯ PDF (Bytes) ---
def create_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    font_file = "arial.ttf"
    if os.path.exists(font_file):
        pdf.add_font("CustomFont", "", font_file); pdf.set_font("CustomFont", "", 14)
        t1, t2 = "СМЕТА ЗАКАЗА - IRON WORKS", f"Материал: {res['name']}"
    else:
        pdf.set_font("Helvetica", "B", 14)
        t1, t2 = "ESTIMATE - IRON WORKS", f"Material: {res['name']}"
    
    pdf.cell(200, 10, txt=t1, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica" if not os.path.exists(font_file) else "CustomFont", "", 12)
    pdf.cell(200, 10, txt=t2, ln=True)
    pdf.cell(200, 10, txt=f"Вес: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Отход: {res['waste']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО: {res['total']:.0f} грн", ln=True)
    return bytes(pdf.output())

# --- 3. БАЗА ДАННЫХ ---
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

# --- 4. ОСНОВНОЙ ИНТЕРФЕЙС ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Металл:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Цена:", ["Розница", "Опт"])
        
        if is_sheet:
            L_sheet, W_sheet = st.number_input("Лист L", 2500.0), st.number_input("Лист W", 1250.0)
            l_det, w_det = st.number_input("Деталь l", 600.0), st.number_input("Деталь w", 400.0)
            qty = st.number_input("Кол-во шт", 1, 5000, 10)
        else:
            rl, rw, rh = st.number_input("Длина L (мм)", 2000.0), st.number_input("Ширина W (мм)", 1000.0), st.number_input("Высота H (мм)", 1200.0)
            stock = st.number_input("Палка (м)", 6.0)
            
        markup = st.slider("Наценка %", 0, 100, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        if is_sheet:
            nx = int(L_sheet // l_det)
            ny = int(W_sheet // w_det)
            on_one = max(1, nx * ny)
            sheets_needed = -(-qty // on_one)
            weight_total = sheets_needed * item['weight']
            base = (sheets_needed * item['p_unit']) if mode == "Розница" else (weight_total/1000 * item['p_ton'])
            waste = ((sheets_needed * L_sheet * W_sheet - qty * l_det * w_det) / (sheets_needed * L_sheet * W_sheet)) * 100
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.1, stock))
            weight_total = pcs * stock * item['weight']
            base = (pcs * stock * item['p_unit']) if mode == "Розница" else (weight_total/1000 * item['p_ton'])
            waste = ((pcs * stock - m_lin) / (pcs * stock)) * 100

        res_total = base * (1 + markup/100)

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sheets_needed if is_sheet else pcs)} ед.")
        c2.metric("Вес", f"{weight_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{res_total:.0f}")

        # --- КАРТА РАСКРОЯ (ТОЛЬКО ДЛЯ ЛИСТА) ---
        if is_sheet:
            st.subheader("✂️ Карта раскроя на одном листе")
            fig_cut = go.Figure()
            # Контур листа
            fig_cut.add_shape(type="rect", x0=0, y0=0, x1=L_sheet, y1=W_sheet, line=dict(color="White", width=3))
            # Детали
            count = 0
            for i in range(nx):
                for j in range(ny):
                    if count < qty:
                        fig_cut.add_shape(type="rect", x0=i*l_det, y0=j*w_det, x1=(i+1)*l_det, y1=(j+1)*w_det, 
                                          fillcolor="rgba(0, 198, 255, 0.5)", line=dict(color="#00c6ff", width=1))
                        count += 1
            fig_cut.update_layout(xaxis_range=[-50, L_sheet+50], yaxis_range=[-50, W_sheet+50], 
                                  width=800, height=450, template="plotly_dark", title=f"Размещение деталей: {min(qty, on_one)} на лист")
            st.plotly_chart(fig_cut, use_container_width=True)

        # --- 3D МОДЕЛЬ ---
        st.subheader("📦 3D Визуализация")
        if is_sheet:
            lx, ly, lz = L_sheet, W_sheet, item['thick']
            # Рисуем пластину (плотный каркас)
            x = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
            y = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
            z = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]
        else:
            lx, ly, lz = rl, rw, rh
            x = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
            y = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
            z = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]

        fig_3d = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=6))])
        fig_3d.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0), paper_bgcolor='#0e1117')
        st.plotly_chart(fig_3d, use_container_width=True)

        # PDF & AutoCAD
        st.divider()
        pdf_bytes = create_pdf({"name": sel, "weight": weight_total, "waste": waste, "total": res_total})
        st.download_button("📥 СКАЧАТЬ СМЕТУ PDF", pdf_bytes, "IronWorks_Smeta.pdf", "application/pdf", use_container_width=True)
        
        st.subheader("📝 Код AutoCAD")
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        