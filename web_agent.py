import streamlit as st
import os
import plotly.graph_objects as go
import re
import math

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v10.3", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-note { background-color: #0e2a47; padding: 15px; border-radius: 10px; border-left: 5px solid #00c6ff; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | 3D NESTING ENGINE v10.3</p></div>', unsafe_allow_html=True)

# --- 2. ПАРСЕР ---
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
                    thick_m = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(thick_m[-1]) if thick_m else 2.0
                    prices[name] = {"weight": weight, "price": price, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        selected_mat = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: 3D ЛИСТ + НЕСТИНГ")
            L_s, W_s = st.number_input("Лист Длина", 2500), st.number_input("Лист Ширина", 1250)
            L_d, W_d = st.number_input("Деталь Длина", 600), st.number_input("Деталь Ширина", 400)
            Qty = st.number_input("Кол-во деталей", 10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: 3D КАРКАС / ТРУБА")
            L_f, W_f, H_f = st.number_input("L (мм)", 2000), st.number_input("W (мм)", 1000), st.number_input("H (мм)", 1200)
            dims = re.findall(r'(\d+)', selected_mat)
            A, B = (int(dims[0]), int(dims[1])) if len(dims)>=2 else (40, 20)
        
        calc = st.button("🚀 ПОСТРОИТЬ В 3D", use_container_width=True)

# --- 4. РАСЧЕТ И ВИЗУАЛИЗАЦИЯ ---
if calc and all_prices:
    if is_sheet:
        # --- 3D ЛИСТ + 3D РАСКРОЙ ---
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 0
        thick = data['thick']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("На листе", f"{on_sheet} шт", f"Толщина {thick}мм")
        c2.metric("Листов", f"{needed} шт", f"Вес пачки {needed*data['weight']:.1f}кг")
        c3.metric("Цена пачки", f"{(needed*data['weight']*data['price']):.0f} грн")

        # 3D Модель (Plotly Mesh3d)
        fig = go.Figure()
        # 1. Лист (голубой параллелепипед)
        fig.add_trace(go.Mesh3d(
            x=[0, L_s, L_s, 0, 0, L_s, L_s, 0],
            y=[0, 0, W_s, W_s, 0, 0, W_s, W_s],
            z=[0, 0, 0, 0, thick, thick, thick, thick],
            color='royalblue', opacity=0.5, flatshading=True, name="Лист"
        ))
        # 2. Детали (оранжевые, лежат НА листе)
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    x0, y0, z0 = c*L_d, r*W_d, thick + 0.1 # Чуть выше листа
                    x1, y1, z1 = (c+1)*L_d, (r+1)*W_d, thick + thick/2 + 0.1
                    fig.add_trace(go.Mesh3d(
                        x=[x0, x1, x1, x0, x0, x1, x1, x0],
                        y=[y0, y0, y1, y1, y0, y0, y1, y1],
                        z=[z0, z0, z0, z0, z1, z1, z1, z1],
                        color='orange', opacity=1.0, flatshading=True, name=f"Деталь {idx+1}"
                    ))
                    idx += 1
        
        fig.update_layout(scene=dict(aspectmode='data', xaxis_title='L', yaxis_title='W', zaxis_title='H'), height=700, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)
        
        st.code(f"(defun c:IronSheet () (command \"_RECTANG\" '(0 0) '({L_s} {W_s})) (princ))", language="lisp")
    else:
        # --- 3D КАРКАС ---
        pure_m = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        w_t = pure_m * 1.05 * data['weight']
        paint = ((A+B)*2/1000) * pure_m * 1.05
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{w_t:.1f} кг"); c2.metric("Метраж", f"{pure_m:.1f} м")
        c3.metric("Малярка", f"{paint:.2f} м²"); c4.metric("Смета", f"{(w_t*data['price']*1.1):.0f} грн")

        # 3D
        fig = go.Figure(data=go.Scatter3d(x=[0,L_f,L_f,0,0,0,L_f,L_f,0,0,0,0,L_f,L_f,L_f,L_f], y=[0,0,W_f,W_f,0,0,0,W_f,W_f,0,W_f,W_f,W_f,W_f,0,0], z=[0,0,0,0,0,H_f,H_f,H_f,H_f,H_f,H_f,0,0,H_f,H_f,0], mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), height=600, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)
        
        st.code(f"(defun c:IronFrame () (command \"_BOX\" '(0 0 0) \"_L\" {L_f} {W_f} {H_f}) (princ))", language="lisp")
        