import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ И ИНТЕРФЕЙС (Красивый заголовок v15.0) ---
st.set_page_config(page_title="IRON WORKS v15.0", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Precision Pack v15.0</h1><p style="color: #00c6ff; font-size: 18px; margin: 0;">Профессиональный расчет и визуализация</p></div>', unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF (BYTES) ---
def create_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    f_file = "arial.ttf"
    if os.path.exists(f_file):
        pdf.add_font("CustomFont", "", f_file); pdf.set_font("CustomFont", "", 14)
        t1, t2 = "ТЕХНИЧЕСКАЯ СМЕТА - IRON WORKS", f"Материал: {res['name']}"
    else:
        pdf.set_font("Helvetica", "B", 14); t1, t2 = "ESTIMATE - IRON WORKS", f"Material: {res['name']}"
    
    pdf.cell(200, 10, txt=t1, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica" if not os.path.exists(f_file) else "CustomFont", "", 12)
    pdf.cell(200, 10, txt=t2, ln=True)
    pdf.cell(200, 10, txt=f"Вес закупки: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Процент отхода: {res['waste']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО К ОПЛАТЕ: {res['total']:.0f} грн", ln=True)
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
        sel = st.selectbox("Материал из базы:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Тип цены:", ["Розница", "Опт (Тонна)"])
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L (мм)", 1.0, 6000.0, 2500.0), st.number_input("Лист W (мм)", 1.0, 6000.0, 1250.0)
            ld, wd = st.number_input("Деталь l (мм)", 1.0, 6000.0, 600.0), st.number_input("Деталь w (мм)", 1.0, 6000.0, 400.0)
            qty = st.number_input("Кол-во шт", 1, 5000, 10)
        else:
            rl, rw, rh = st.number_input("Длина L (мм)", 1.0, 10000.0, 2000.0), st.number_input("Ширина W (мм)", 1.0, 10000.0, 1000.0), st.number_input("Высота H (мм)", 1.0, 10000.0, 1200.0)
            stock = st.number_input("Палка проката (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 300, 15)
        calc_btn = st.button("🚀 РОЗРАХУВАТЬ СМЕТУ", use_container_width=True)

    if calc_btn:
        # Логика расчета
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_n = -(-qty // max(1, nx * ny))
            w_total = sh_n * item['weight']
            base_p = (sh_n * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste_p = ((sh_n * Ls * Ws - qty * ld * wd) / (sh_n * Ls * Ws)) * 100
            lx, ly, lz = Ls, Ws, item['thick']
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.01, stock))
            w_total = pcs * stock * item['weight']
            base_p = (pcs * stock * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste_p = ((pcs * stock - m_lin) / (pcs * stock)) * 100
            lx, ly, lz = rl, rw, rh

        total_final = base_p * (1 + markup/100)

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_n if is_sheet else pcs)} ед.")
        c2.metric("Общий вес", f"{w_total:.1f} кг")
        c3.metric("Отход", f"{waste_p:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_final:.0f}")

        # --- КРИТИЧЕСКИЙ КОРРЕКТИРУЮЩИЙ 3D МОДУЛЬ ---
        st.subheader("📦 Precision 3D Visualizer")
        fig = go.Figure()

        # Данные визуализации (одинаковые для обоих типов)
        xc = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
        yc = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
        zc = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]

        if is_sheet:
            # --- ЛИСТ: Прозрачная плита (Thick Z принудительно зажат) ---
            fig.add_trace(go.Mesh3d(
                x=[0, lx, lx, 0, 0, lx, lx, 0], y=[0, 0, ly, ly, 0, 0, ly, ly], z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#00c6ff', opacity=0.7, flatshading=True, name="Лист"
            ))
            # Четкие грани (wireframe)
            fig.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=3)))

            # НАСТРОЙКА ПРОПОРЦИЙ: ПОДАВЛЕНИЕ СКАЛИРОВАНИЯ ПО Z
            # max_dim = max(lx, ly)
            fig.update_layout(
                scene=dict(
                    xaxis_title='L (мм)', yaxis_title='W (мм)', zaxis_title='Thick (мм)',
                    aspectmode='manual',
                    aspectratio=dict(x=1.0, y=(ly/lx), z=0.05), # ПРИНУДИТЕЛЬНО ПЛОСКИЙ РАКУРС
                    camera=dict(eye=dict(x=1.8, y=1.2, z=0.8)) # Ракурс ISO сверху
                ),
                height=650, paper_bgcolor='#0e1117'
            )
        else:
            # --- ИЗДЕЛИЕ: Обычный каркас (сохраняем пропорции данных) ---
            fig.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))
            
            fig.update_layout(
                scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
                height=650, paper_bgcolor='#0e1117'
            )

        st.plotly_chart(fig, use_container_width=True)

        # PDF & AutoCAD
        st.divider()
        pdf_data = create_pdf({"name": sel, "weight": w_total, "waste": waste_p, "total": total_final})
        st.download_button("📥 СКАЧАТЬ СМЕТУ PDF", pdf_data, "IronWorks_Report.pdf", "application/pdf", use_container_width=True)
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        