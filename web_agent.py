import streamlit as st
import os
import plotly.graph_objects as go
import re
import math

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v10.2", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-note { background-color: #0e2a47; padding: 15px; border-radius: 10px; border-left: 5px solid #00c6ff; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | FINAL HYBRID ENGINE v10.2</p></div>', unsafe_allow_html=True)

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
            st.success("📦 РЕЖИМ: ЛИСТ")
            L_s = st.number_input("Лист Длина", value=2500)
            W_s = st.number_input("Лист Ширина", value=1250)
            L_d = st.number_input("Деталь Длина", value=600)
            W_d = st.number_input("Деталь Ширина", value=400)
            Qty = st.number_input("Кол-во деталей", value=10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: ТРУБА")
            L_f = st.number_input("Длина L", value=2000)
            W_f = st.number_input("Ширина W", value=1000)
            H_f = st.number_input("Высота H", value=1200)
            dims = re.findall(r'(\d+)', selected_mat)
            A = int(dims[0]) if len(dims)>=1 else 40
            B = int(dims[1]) if len(dims)>=2 else 20
        
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 4. ЛОГИКА ---
if calc and all_prices:
    if is_sheet:
        # --- РАСКРОЙ + 3D ЛИСТ ---
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("На листе", f"{on_sheet} шт")
        c2.metric("Всего листов", f"{needed} шт")
        c3.metric("Вес пачки", f"{(data['weight'] * needed):.1f} кг")

        # Карта раскроя (Plotly)
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=L_s, y1=W_s, line=dict(color="Cyan", width=3), fillcolor="rgba(0,255,255,0.1)")
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    fig.add_shape(type="rect", x0=c*L_d, y0=r*W_d, x1=(c+1)*L_d, y1=(r+1)*W_d, line=dict(color="White"), fillcolor="Orange")
                    idx += 1
        fig.update_layout(xaxis=dict(range=[-50, L_s+50]), yaxis=dict(range=[-50, W_s+50]), height=500, paper_bgcolor='#0e1117')
        st.plotly_chart(fig)
        
        st.info(f"💡 Совет: Для листа {data['thick']}мм используйте ток {(data['thick']*35):.0f}А.")
        st.code(f"(defun c:IronSheet () (command \"_RECTANG\" '(0 0) '({L_s} {W_s})) (princ))", language="lisp")

    else:
        # --- РАСЧЕТ ТРУБ ---
        m_pure = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        m_real = m_pure * 1.05
        w_total = m_real * data['weight']
        cost = (w_total * data['price']) * 1.10
        paint = ((A+B)*2/1000) * m_real

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{w_total:.1f} кг")
        c2.metric("Метраж", f"{m_real:.1f} м")
        c3.metric("Малярка", f"{paint:.2f} м²")
        c4.metric("Смета", f"{cost:.0f} грн")

        # 3D Каркас
        fig = go.Figure(data=go.Scatter3d(x=[0,L_f,L_f,0,0,0,L_f,L_f,0,0,0,0,L_f,L_f,L_f,L_f], y=[0,0,W_f,W_f,0,0,0,W_f,W_f,0,W_f,W_f,W_f,W_f,0,0], z=[0,0,0,0,0,H_f,H_f,H_f,H_f,H_f,H_f,0,0,H_f,H_f,0], mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), height=600, paper_bgcolor='#0e1117')
        st.plotly_chart(fig)

        # Инженерный блок
        st.markdown(f"""<div class="eng-note"><b>🛠️ Технология для трубы со стенкой {data['thick']}мм:</b><br>
        • Риск деформации: {"ВЫСОКИЙ" if data['thick'] < 2.0 else "СТАНДАРТНЫЙ"}<br>
        • Режим: {"Сварка короткими швами с остыванием" if data['thick'] < 2.0 else "Сплошной шов, ток 120А"}<br>
        • Примечание: Соблюдайте диагонали перед обваркой!</div>""", unsafe_allow_html=True)
        
        st.code(f"(defun c:IronFrame () (command \"_BOX\" '(0 0 0) \"_L\" {L_f} {W_f} {H_f}) (princ))", language="lisp")
        