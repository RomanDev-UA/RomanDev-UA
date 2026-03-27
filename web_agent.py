import streamlit as st
import os
import plotly.graph_objects as go
import re

# --- 1. СТИЛИ И ЗАГОЛОВОК ---
st.set_page_config(page_title="IRON WORKS v10.1", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #3e445b; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | 3D SHEET & FRAME ENGINE v10.1</p></div>', unsafe_allow_html=True)

# --- 2. ПАРСЕР ПРАЙСА ---
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
                    # Ищем толщину (мм) в названии
                    thick_match = re.findall(r'(\d+\.\d+|\d+)\s*мм', name.lower())
                    if not thick_match: thick_match = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(thick_match[-1]) if thick_match else 2.0
                    prices[name] = {"weight": weight, "price": price, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("⚙️ ВВОД ДАННЫХ")
    if all_prices:
        selected_mat = st.selectbox("ВЫБОР МАТЕРИАЛА:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: 3D ЛИСТ")
            L_s, W_s = st.number_input("Длина листа (мм)", 2500), st.number_input("Ширина листа (мм)", 1250)
            Qty = st.number_input("Кол-во листов (шт)", 1, 100, 1)
        else:
            st.info("🏗️ РЕЖИМ: 3D КАРКАС")
            L_f, W_f, H_f = st.number_input("Длина L (мм)", 2500), st.number_input("Ширина W (мм)", 1200), st.number_input("Высота H (мм)", 1000)
        
        calc = st.button("🚀 ПОСТРОИТЬ В 3D", use_container_width=True)

# --- 4. РАСЧЕТ И ВИЗУАЛИЗАЦИЯ ---
if calc and all_prices:
    if is_sheet:
        # ЛОГИКА 3D ЛИСТА
        thick = data['thick']
        total_w = data['weight'] * Qty
        total_c = total_w * data['price']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Толщина", f"{thick} мм")
        c2.metric("Общий вес", f"{total_w:.1f} кг")
        c3.metric("Цена", f"{total_c:.0f} грн")

        # Рисуем 3D Лист (как параллелепипед)
        fig = go.Figure()
        # Нижняя грань
        fig.add_trace(go.Mesh3d(
            x=[0, L_s, L_s, 0, 0, L_s, L_s, 0],
            y=[0, 0, W_s, W_s, 0, 0, W_s, W_s],
            z=[0, 0, 0, 0, thick, thick, thick, thick],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color='royalblue', opacity=0.7, name=f"Лист {thick}мм"
        ))
        fig.update_layout(scene=dict(aspectmode='data', xaxis_title='Длина', yaxis_title='Ширина', zaxis_title='Толщина'), paper_bgcolor='#0e1117', height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Совет по сварке
        if thick < 2.0:
            st.warning(f"⚠️ Лист {thick}мм очень тонкий! Варить на малых токах (30-50А), короткими стежками.")
        elif thick >= 4.0:
            st.info(f"💡 Лист {thick}мм массивный. Для качественного шва делай разделку кромок под 45°.")

    else:
        # ЛОГИКА 3D КАРКАСА (как в v9.9)
        pure_m = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        weight_t = pure_m * 1.05 * data['weight']
        
        st.metric("Параметры каркаса", f"{weight_t:.1f} кг | {pure_m:.1f} м")
        
        x_c = [0,L_f,L_f,0,0,0,L_f,L_f,0,0,0,0,L_f,L_f,L_f,L_f]
        y_c = [0,0,W_f,W_f,0,0,0,W_f,W_f,0,W_f,W_f,W_f,W_f,0,0]
        z_c = [0,0,0,0,0,H_f,H_f,H_f,H_f,H_f,H_f,0,0,H_f,H_f,0]
        
        fig = go.Figure(data=go.Scatter3d(x=x_c, y=y_c, z=z_c, mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), paper_bgcolor='#0e1117', height=600)
        st.plotly_chart(fig, use_container_width=True)

    # ОБЩАЯ КНОПКА LISP
    st.subheader("🤖 Код для nanoCAD")
    if is_sheet:
        lisp = f"(defun c:IronSheet () (command \"_BOX\" '(0 0 0) \"_L\" {float(L_s)} {float(W_s)} {float(thick)}) (princ))"
    else:
        lisp = f"(defun c:IronFrame () (command \"_BOX\" '(0 0 0) \"_L\" {float(L_f)} {float(W_f)} {float(H_f)}) (princ))"
    st.code(lisp, language="lisp")
    