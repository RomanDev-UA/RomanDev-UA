import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v14.8", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Engineering v14.8</h1></div>', unsafe_allow_html=True)

# --- 2. ЛОГИКА СВАРКИ ---
def get_weld_advice(thick):
    if thick < 2.0:
        return {"amp": "40-65А", "electr": "2.0 мм", "text": "Сварка короткими прихватками, избегайте перегрева."}
    elif thick <= 4.0:
        return {"amp": "90-120А", "electr": "3.0 мм", "text": "Стабильная дуга, шов в один проход."}
    else:
        return {"amp": "160-190А", "electr": "4.0 мм", "text": "Требуется разделка кромок и многослойный шов."}

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

# --- 4. ИНТЕРФЕЙС ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Материал:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Цена:", ["Розница", "Опт"])
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L", 1.0, 6000.0, 2500.0), st.number_input("Лист W", 1.0, 6000.0, 1250.0)
            ld, wd = st.number_input("Деталь l", 1.0, 6000.0, 600.0), st.number_input("Деталь w", 1.0, 6000.0, 400.0)
            qty = st.number_input("Кол-во", 1, 1000, 10)
        else:
            rl, rw, rh = st.number_input("Длина изделия", 1.0, 10000.0, 2000.0), st.number_input("Ширина", 1.0, 10000.0, 1000.0), st.number_input("Высота", 1.0, 10000.0, 1200.0)
            stock = st.number_input("Палка (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 200, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        w_adv = get_weld_advice(item['thick'])
        
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_n = -(-qty // max(1, nx * ny))
            w_total = sh_n * item['weight']
            base = (sh_n * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((sh_n * Ls * Ws - qty * ld * wd) / (sh_n * Ls * Ws)) * 100
            lx, ly, lz = Ls, Ws, item['thick']
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.01, stock))
            w_total = pcs * stock * item['weight']
            base = (pcs * stock * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((pcs * stock - m_lin) / (pcs * stock)) * 100
            lx, ly, lz = rl, rw, rh

        total_price = base * (1 + markup/100)

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_n if is_sheet else pcs)} ед.")
        c2.metric("Вес", f"{w_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # ИНЖЕНЕРНЫЙ БЛОК
        st.subheader("🛠️ Инженерный расчет")
        st.markdown(f"""
            <div class="eng-card">
                <b>Толщина металла:</b> {item['thick']} мм<br>
                <b>Рекомендуемый ток:</b> {w_adv['amp']}<br>
                <b>Электрод:</b> {w_adv['electr']}<br>
                <b>Технология:</b> {w_adv['text']}
            </div>
        """, unsafe_allow_html=True)

        # 3D МОДЕЛИРОВАНИЕ (РАЗДЕЛЬНОЕ)
        st.subheader("📦 3D Визуализация")
        fig = go.Figure()
        
        if is_sheet:
            # Только плита для листа
            fig.add_trace(go.Mesh3d(
                x=[0, lx, lx, 0, 0, lx, lx, 0], y=[0, 0, ly, ly, 0, 0, ly, ly], z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#00c6ff', opacity=0.8, flatshading=True
            ))
        else:
            # Только каркас для изделия
            xc = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
            yc = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
            zc = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]
            fig.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))

        fig.update_layout(scene=dict(aspectmode='data', camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))), height=500, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        