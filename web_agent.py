import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v14.6", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0;">🏗️ IRON WORKS | Professional 3D v14.6</h1></div>', unsafe_allow_html=True)

# --- 2. PDF ---
def create_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    f_file = "arial.ttf"
    if os.path.exists(f_file):
        pdf.add_font("CustomFont", "", f_file); pdf.set_font("CustomFont", "", 14)
        t1, t2 = "СМЕТА ЗАКАЗА - IRON WORKS", f"Материал: {res['name']}"
    else:
        pdf.set_font("Helvetica", "B", 14)
        t1, t2 = "ESTIMATE - IRON WORKS", f"Material: {res['name']}"
    pdf.cell(200, 10, txt=t1, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica" if not os.path.exists(f_file) else "CustomFont", "", 12)
    pdf.cell(200, 10, txt=f"{t2}\nВес: {res['weight']:.1f} кг\nОтход: {res['waste']:.1f}%\nИТОГО: {res['total']:.0f} грн", ln=True)
    return bytes(pdf.output())

# --- 3. DATABASE ---
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

# --- 4. INTERFACE ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод")
        sel = st.selectbox("Материал:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Цена:", ["Розница", "Опт"])
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L", 1.0, 6000.0, 2500.0), st.number_input("Лист W", 1.0, 6000.0, 1250.0)
            ld, wd = st.number_input("Деталь l", 1.0, 6000.0, 600.0), st.number_input("Деталь w", 1.0, 6000.0, 400.0)
            qty = st.number_input("Кол-во шт", 1, 5000, 10)
        else:
            rl, rw, rh = st.number_input("L изделия", 1.0, 10000.0, 2000.0), st.number_input("W изделия", 1.0, 10000.0, 1000.0), st.number_input("H изделия", 1.0, 10000.0, 1200.0)
            stock = st.number_input("Длина проката (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 300, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_n = -(-qty // max(1, nx * ny))
            w_t = sh_n * item['weight']
            base = (sh_n * item['p_unit']) if mode == "Розница" else (w_t/1000 * item['p_ton'])
            waste = ((sh_n * Ls * Ws - qty * ld * wd) / (sh_n * Ls * Ws)) * 100
            lx, ly, lz = Ls, Ws, item['thick']
        else:
            m_l = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_l // max(0.01, stock))
            w_t = pcs * stock * item['weight']
            base = (pcs * stock * item['p_unit']) if mode == "Розница" else (w_t/1000 * item['p_ton'])
            waste = ((pcs * stock - m_l) / (pcs * stock)) * 100
            lx, ly, lz = rl, rw, rh

        total = base * (1 + markup/100)
        st.metric("ИТОГО ГРН", f"{total:.0f}", f"Вес: {w_t:.1f} кг | Отход: {waste:.1f}%")

        # --- 3D ВИЗУАЛИЗАЦИЯ ---
        st.subheader("📦 3D Модель объекта")
        fig = go.Figure()

        if is_sheet:
            # РИСУЕМ ОБЪЕМНЫЙ ЛИСТ (MESH)
            fig.add_trace(go.Mesh3d(
                x=[0, lx, lx, 0, 0, lx, lx, 0],
                y=[0, 0, ly, ly, 0, 0, ly, ly],
                z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#00c6ff', opacity=0.7, flatshading=True, name="Лист"
            ))
        else:
            # РИСУЕМ КАРКАС ИЗ ЛИНИЙ
            x_c = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
            y_c = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
            z_c = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]
            fig.add_trace(go.Scatter3d(x=x_c, y=y_c, z=z_c, mode='lines', line=dict(color='#00c6ff', width=6)))

        # Настройка камеры (чтобы сразу видеть объем)
        fig.update_layout(
            scene=dict(
                xaxis_title='L (мм)', yaxis_title='W (мм)', zaxis_title='H (мм)',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
                aspectmode='data'
            ),
            height=600, paper_bgcolor='#0e1117'
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- КАРТА РАСКРОЯ (ТОЛЬКО ДЛЯ ЛИСТА) ---
        if is_sheet:
            st.subheader("✂️ Карта размещения деталей (2D)")
            fig_2d = go.Figure()
            fig_2d.add_shape(type="rect", x0=0, y0=0, x1=Ls, y1=Ws, line=dict(color="White", width=2))
            count = 0
            for i in range(nx):
                for j in range(ny):
                    if count < qty:
                        fig_2d.add_shape(type="rect", x0=i*ld, y0=j*wd, x1=(i+1)*ld, y1=(j+1)*wd, fillcolor="#00c6ff", opacity=0.3)
                        count += 1
            fig_2d.update_layout(xaxis_range=[-50, Ls+50], yaxis_range=[-50, Ws+50], template="plotly_dark", height=400)
            st.plotly_chart(fig_2d, use_container_width=True)

        # ФИНАЛ
        st.divider()
        pdf_d = create_pdf({"name": sel, "weight": w_t, "waste": waste, "total": total})
        st.download_button("📥 СКАЧАТЬ PDF СМЕТУ", pdf_d, "IronWorks.pdf", "application/pdf", use_container_width=True)
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        