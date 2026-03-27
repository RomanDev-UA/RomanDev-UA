import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v15.1", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | 3D Nesting v15.1</h1></div>', unsafe_allow_html=True)

# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def create_pdf(res, w_info):
    pdf = FPDF()
    pdf.add_page()
    f_file = "arial.ttf"
    if os.path.exists(f_file):
        pdf.add_font("CustomFont", "", f_file); pdf.set_font("CustomFont", "", 14)
        t1 = "ТЕХНИЧЕСКАЯ СМЕТА - IRON WORKS"
    else:
        pdf.set_font("Helvetica", "B", 14); t1 = "ESTIMATE - IRON WORKS"
    
    pdf.cell(200, 10, txt=t1, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica" if not os.path.exists(f_file) else "CustomFont", "", 12)
    pdf.cell(200, 10, txt=f"Материал: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Вес закупки: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО: {res['total']:.0f} грн", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Сварка: {w_info['amp']} / {w_info['electr']}")
    return bytes(pdf.output())

def get_weld_tech(thick):
    if thick < 2.0: return {"amp": "45-65А", "electr": "2.0 мм", "meth": "Прихватки"}
    elif thick <= 4.0: return {"amp": "90-130А", "electr": "3.0 мм", "meth": "Сплошной шов"}
    else: return {"amp": "160-200А", "electr": "4.0 мм", "meth": "Разделка кромок"}

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
                    name, w, p_u, p_t = parts[0].strip(), float(parts[1].replace(',','.')), float(parts[2].replace(',','.')), float(parts[3].replace(',','.'))
                    thick = float(re.findall(r'(\d+\.\d+|\d+)', name)[-1]) if re.findall(r'(\d+\.\d+|\d+)', name) else 2.0
                    catalog[name] = {"weight": w, "p_unit": p_u, "p_ton": p_t, "thick": thick}
                except: continue
    return catalog

db = load_db()

# --- 3. ИНТЕРФЕЙС ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Материал:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L", 10.0, 6000.0, 2500.0), st.number_input("Лист W", 10.0, 3000.0, 1250.0)
            ld, wd = st.number_input("Деталь l", 10.0, 6000.0, 600.0), st.number_input("Деталь w", 10.0, 3000.0, 400.0)
            qty = st.number_input("Кол-во (шт)", 1, 1000, 12)
        else:
            rl, rw, rh = st.number_input("L изделия", 10.0, 10000.0, 2000.0), st.number_input("W", 10.0, 10000.0, 1000.0), st.number_input("H", 10.0, 10000.0, 1200.0)
            stock = st.number_input("Палка (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 300, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        w_tech = get_weld_tech(item['thick'])
        
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            on_one = max(1, nx * ny)
            sh_needed = -(-qty // on_one)
            weight_total = sh_needed * item['weight']
            total_price = (sh_needed * item['p_unit']) * (1 + markup/100)
            waste = ((sh_needed * Ls * Ws - qty * ld * wd) / (sh_needed * Ls * Ws)) * 100
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.01, stock))
            weight_total = pcs * stock * item['weight']
            total_price = (pcs * stock * item['p_unit']) * (1 + markup/100)
            waste = ((pcs * stock - m_lin) / (pcs * stock)) * 100

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_needed if is_sheet else pcs)} ед.")
        c2.metric("Вес", f"{weight_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # Сварка
        st.markdown(f'<div class="eng-card"><b>ПАРАМЕТРЫ СВАРКИ:</b> Ток {w_tech["amp"]}, Электрод {w_tech["electr"]}, {w_tech["meth"]}</div>', unsafe_allow_html=True)

        # --- 4. МОДЕРНИЗИРОВАННЫЙ 3D МОДУЛЬ ---
        st.subheader("📦 3D Визуализация и Раскрой")
        fig = go.Figure()

        if is_sheet:
            # 1. ОСНОВНОЙ ЛИСТ (Mesh3d)
            lz = item['thick']
            fig.add_trace(go.Mesh3d(
                x=[0, Ls, Ls, 0, 0, Ls, Ls, 0], y=[0, 0, Ws, Ws, 0, 0, Ws, Ws], z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#1a1a1a', opacity=0.5, name="Лист-заготовка"
            ))

            # 2. ДЕТАЛИ НА ЛИСТЕ (3D Wireframe каждой детали)
            d_count = 0
            for i in range(nx):
                for j in range(ny):
                    if d_count < qty:
                        x0, x1 = i * ld, (i+1) * ld
                        y0, y1 = j * wd, (j+1) * wd
                        # Рисуем контур детали чуть выше поверхности листа
                        fig.add_trace(go.Scatter3d(
                            x=[x0, x1, x1, x0, x0], y=[y0, y0, y1, y1, y0], z=[lz+0.5]*5,
                            mode='lines', line=dict(color='#00c6ff', width=4), showlegend=False
                        ))
                        d_count += 1
            
            # Настройка пропорций (ЧТОБЫ НЕ БЫЛО КУБА)
            fig.update_layout(
                scene=dict(
                    aspectmode='manual',
                    aspectratio=dict(x=1, y=Ws/Ls, z=0.1), # Сплющиваем Z
                    xaxis_title="L (мм)", yaxis_title="W (мм)", zaxis_title="T",
                    camera=dict(eye=dict(x=1.2, y=1.2, z=0.6))
                )
            )
        else:
            # Обычный каркас для металлоконструкций
            lx, ly, lz = rl, rw, rh
            xc = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
            yc = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
            zc = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]
            fig.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))
            fig.update_layout(scene=dict(aspectmode='data'))

        fig.update_layout(height=600, paper_bgcolor='#0e1117', margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

        # PDF & AutoCAD
        st.divider()
        pdf_b = create_pdf({"name": sel, "weight": weight_total, "waste": waste, "total": total_price}, w_tech)
        st.download_button("📥 СКАЧАТЬ СМЕТУ PDF", pdf_b, "IronWorks.pdf", "application/pdf", use_container_width=True)
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {Ls if is_sheet else rl} {Ws if is_sheet else rw} {item['thick'] if is_sheet else rh}) (princ))")
        