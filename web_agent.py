import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. НАСТРОЙКИ ИНТЕРФЕЙСА ---
st.set_page_config(page_title="IRON WORKS v15.5", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | 3D Nesting v15.5</h1></div>', unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF ---
def create_pdf(res, w_info):
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
    pdf.multi_cell(0, 10, txt=f"{t2}\nВес: {res['weight']:.1f} кг\nОтход: {res['waste']:.1f}%\nИТОГО: {res['total']:.0f} грн\n\nСВАРКА:\nТок: {w_info['amp']}, Электрод: {w_info['electr']}")
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
                    name, weight, p_unit, p_ton = parts[0].strip(), float(parts[1].replace(',','.')), float(parts[2].replace(',','.')), float(parts[3].replace(',','.'))
                    thick = float(re.findall(r'(\d+\.\d+|\d+)', name)[-1]) if re.findall(r'(\d+\.\d+|\d+)', name) else 2.0
                    catalog[name] = {"weight": weight, "p_unit": p_unit, "p_ton": p_ton, "thick": thick}
                except: continue
    return catalog

db = load_db()

# --- 4. ОСНОВНОЙ БЛОК ---
if db:
    with st.sidebar:
        st.header("⚙️ Параметры")
        sel = st.selectbox("Металл:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L", 1.0, 6000.0, 2500.0), st.number_input("Лист W", 1.0, 6000.0, 1250.0)
            ld, wd = st.number_input("Деталь l", 1.0, 6000.0, 600.0), st.number_input("Деталь w", 1.0, 6000.0, 400.0)
            qty = st.number_input("Кол-во шт", 1, 5000, 10)
        else:
            rl, rw, rh = st.number_input("L (мм)", 1.0, 10000.0, 2000.0), st.number_input("W", 1.0, 10000.0, 1000.0), st.number_input("H", 1.0, 10000.0, 1200.0)
            stock = st.number_input("Палка (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 300, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        # Логика калькулятора
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            on_sheet = max(1, nx * ny)
            sh_n = -(-qty // on_sheet)
            weight_total = sh_n * item['weight']
            price = (sh_n * item['p_unit']) * (1 + markup/100)
            waste = ((sh_n * Ls * Ws - qty * ld * wd) / (sh_n * Ls * Ws)) * 100
        else:
            m_total = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_total // max(0.01, stock))
            weight_total = pcs * stock * item['weight']
            price = (pcs * stock * item['p_unit']) * (1 + markup/100)
            waste = ((pcs * stock - m_total) / (pcs * stock)) * 100

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_n if is_sheet else pcs)} ед.")
        c2.metric("Вес", f"{weight_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{price:.0f}")

        # Сварка
        w_adv = {"amp": "90-130А", "electr": "3.0 мм"} if item['thick'] > 1.8 else {"amp": "45-65А", "electr": "2.0 мм"}
        st.markdown(f'<div class="eng-card">🛠️ <b>СВАРКА:</b> Ток {w_adv["amp"]}, Электрод {w_adv["electr"]} (Толщина {item["thick"]} мм)</div>', unsafe_allow_html=True)

        # --- КАРТА РАСКРОЯ (2D) ---
        if is_sheet:
            st.subheader("✂️ Карта раскроя деталей на листе")
            fig_nest = go.Figure()
            # Лист
            fig_nest.add_shape(type="rect", x0=0, y0=0, x1=Ls, y1=Ws, line=dict(color="White", width=3))
            # Детали
            d_idx = 0
            for i in range(nx):
                for j in range(ny):
                    if d_idx < qty:
                        fig_nest.add_shape(type="rect", x0=i*ld, y0=j*wd, x1=(i+1)*ld, y1=(j+1)*wd, 
                                          fillcolor="#00c6ff", opacity=0.5, line=dict(color="#00c6ff", width=1))
                        d_idx += 1
            fig_nest.update_layout(xaxis_range=[-100, Ls+100], yaxis_range=[-100, Ws+100], template="plotly_dark", height=400)
            st.plotly_chart(fig_nest, use_container_width=True)

        # --- 3D ВИЗУАЛИЗАЦИЯ (ВОЗВРАТ ПЛОСКОГО ЛИСТА) ---
        st.subheader("📦 3D Модель заготовки")
        fig3d = go.Figure()
        lx, ly, lz = (Ls, Ws, item['thick']) if is_sheet else (rl, rw, rh)

        if is_sheet:
            # Рисуем закрашенную плиту
            fig3d.add_trace(go.Mesh3d(
                x=[0, lx, lx, 0, 0, lx, lx, 0], y=[0, 0, ly, ly, 0, 0, ly, ly], z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#00c6ff', opacity=0.8, flatshading=True
            ))
            # Принудительно зажимаем ракурс, чтобы не было КУБА
            v_z = 0.05 * max(lx, ly)
            fig3d.update_layout(scene=dict(aspectmode='manual', aspectratio=dict(x=1, y=ly/lx, z=v_z/max(lx,ly)), 
                                         camera=dict(eye=dict(x=1.5, y=1.5, z=0.5))))
        else:
            # Каркас
            xc, yc, zc = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0], [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly], [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]
            fig3d.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))
            fig3d.update_layout(scene=dict(aspectmode='data'))

        fig3d.update_layout(height=600, paper_bgcolor='#0e1117', margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig3d, use_container_width=True)

        # Файлы
        st.divider()
        pdf_b = create_pdf({"name": sel, "weight": weight_total, "waste": waste, "total": price}, w_adv)
        st.download_button("📥 СМЕТА PDF", pdf_b, "Report.pdf", "application/pdf", use_container_width=True)
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        