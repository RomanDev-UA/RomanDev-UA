import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. ГРАФИЧЕСКАЯ ОБОЛОЧКА ---
st.set_page_config(page_title="IRON WORKS v15.6", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 20px; }
    .section-head { color: #00c6ff; font-weight: bold; font-size: 18px; margin-top: 15px; border-bottom: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-size: 28px;">🏗️ IRON WORKS | Professional Interface v15.6</h1></div>', unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ И ТЕХНОЛОГИИ ---
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

def get_weld_tech(thick):
    if thick < 1.8: return {"amp": "40-60А", "electr": "2.0 мм", "meth": "Прихватки (короткая дуга)"}
    elif thick <= 4.0: return {"amp": "90-130А", "electr": "3.0 мм", "meth": "Непрерывный шов (углом назад)"}
    else: return {"amp": "160-200А", "electr": "4.0 мм", "meth": "Многослойный шов + разделка"}

db = load_db()

# --- 3. БОКОВАЯ ПАНЕЛЬ С ЧИТАБЕЛЬНЫМИ ПАРАМЕТРАМИ ---
if db:
    with st.sidebar:
        st.markdown('<p class="section-head">📦 1. ВЫБОР МАТЕРИАЛА</p>', unsafe_allow_html=True)
        sel = st.selectbox("Номенклатура из базы:", list(db.keys()), help="Выберите позицию из вашего прайса prices.txt")
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Расчетная цена:", ["Розница (за шт/м)", "Опт (за тонну)"])

        if is_sheet:
            st.markdown('<p class="section-head">📐 2. ГАБАРИТЫ ЛИСТА (мм)</p>', unsafe_allow_html=True)
            Ls = st.number_input("Длина листа (L)", 100.0, 6000.0, 2500.0, step=50.0)
            Ws = st.number_input("Ширина листа (W)", 100.0, 3000.0, 1250.0, step=50.0)
            
            st.markdown('<p class="section-head">✂️ 3. ПАРАМЕТРЫ ДЕТАЛИ (мм)</p>', unsafe_allow_html=True)
            ld = st.number_input("Длина детали (l)", 10.0, 6000.0, 600.0, step=10.0)
            wd = st.number_input("Ширина детали (w)", 10.0, 3000.0, 400.0, step=10.0)
            qty = st.number_input("Требуемое количество (шт)", 1, 5000, 12)
        else:
            st.markdown('<p class="section-head">🏗️ 2. ГАБАРИТЫ ИЗДЕЛИЯ (мм)</p>', unsafe_allow_html=True)
            rl = st.number_input("Длина каркаса (L)", 100.0, 10000.0, 2000.0, step=100.0)
            rw = st.number_input("Ширина каркаса (W)", 100.0, 10000.0, 1000.0, step=100.0)
            rh = st.number_input("Высота каркаса (H)", 100.0, 10000.0, 1200.0, step=100.0)
            stock = st.number_input("Заводская длина палки (м)", 1.0, 12.0, 6.0)

        st.markdown('<p class="section-head">💰 4. ЭКОНОМИКА</p>', unsafe_allow_html=True)
        markup = st.slider("Наценка производства (%)", 0, 200, 15)
        
        calc_btn = st.button("🚀 ВЫПОЛНИТЬ РАСЧЕТ", use_container_width=True)

    # --- 4. ЛОГИКА И ВИЗУАЛИЗАЦИЯ ---
    if calc_btn:
        w_tech = get_weld_tech(item['thick'])
        
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_needed = -(-qty // max(1, nx * ny))
            weight_total = sh_needed * item['weight']
            price_base = (sh_needed * item['p_unit']) if mode == "Розница" else (weight_total/1000 * item['p_ton'])
            waste = ((sh_needed * Ls * Ws - qty * ld * wd) / (sh_needed * Ls * Ws)) * 100
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.01, stock))
            weight_total = pcs * stock * item['weight']
            price_base = (pcs * stock * item['p_unit']) if mode == "Розница" else (weight_total/1000 * item['p_ton'])
            waste = ((pcs * stock - m_lin) / (pcs * stock)) * 100

        total_final = price_base * (1 + markup/100)

        # Результаты
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_needed if is_sheet else pcs)} ед.")
        c2.metric("Общий вес", f"{weight_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_final:.0f}")

        # Инженерная карточка
        st.markdown(f"""
            <div class="eng-card">
                <b>Инженерные параметры сварки:</b><br>
                Металл: {item['thick']} мм | Ток: {w_tech['amp']} | Электрод: {w_tech['electr']} | Метод: {w_tech['meth']}
            </div>
        """, unsafe_allow_html=True)

        # РАСКРОЙ И 3D
        tab1, tab2 = st.tabs(["✂️ Карта раскроя (2D)", "📦 3D Модель"])
        
        with tab1:
            if is_sheet:
                fig2d = go.Figure()
                fig2d.add_shape(type="rect", x0=0, y0=0, x1=Ls, y1=Ws, line=dict(color="White", width=3))
                d_idx = 0
                for i in range(nx):
                    for j in range(ny):
                        if d_idx < qty:
                            fig2d.add_shape(type="rect", x0=i*ld, y0=j*wd, x1=(i+1)*ld, y1=(j+1)*wd, 
                                           fillcolor="#00c6ff", opacity=0.5, line=dict(color="#00c6ff", width=1))
                            d_idx += 1
                fig2d.update_layout(xaxis_title="L (мм)", yaxis_title="W (мм)", template="plotly_dark", height=500)
                st.plotly_chart(fig2d, use_container_width=True)
            else:
                st.info("Карта раскроя доступна только для листового металла.")

        with tab2:
            fig3d = go.Figure()
            lx, ly, lz = (Ls, Ws, item['thick']) if is_sheet else (rl, rw, rh)
            if is_sheet:
                fig3d.add_trace(go.Mesh3d(
                    x=[0,lx,lx,0,0,lx,lx,0], y=[0,0,ly,ly,0,0,ly,ly], z=[0,0,0,0,lz,lz, lz, lz],
                    i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                    color='#00c6ff', opacity=0.8
                ))
                v_z = 0.05 * max(lx, ly)
                fig3d.update_layout(scene=dict(aspectmode='manual', aspectratio=dict(x=1, y=ly/lx, z=v_z/max(lx,ly))))
            else:
                xc, yc, zc = [0,lx,lx,0,0,0,lx,lx,0,0,None,lx,lx,None,lx,lx,None,0,0],[0,0,ly,ly,0,0,0,ly,ly,0,None,0,0,None,ly,ly,None,ly,ly],[0,0,0,0,0,lz,lz,lz,lz,lz,None,0,lz,None,0,lz,None,0,lz]
                fig3d.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))
            
            fig3d.update_layout(height=600, paper_bgcolor='#0e1117', margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig3d, use_container_width=True)

        st.divider()
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
        