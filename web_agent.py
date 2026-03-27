import streamlit as st
import os
import plotly.graph_objects as go
import re
import math

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v9.9", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .brand-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px; }
    .brand-title { color: white !important; font-size: 42px; font-weight: 900; margin: 0; }
    .brand-subtitle { color: #00c6ff !important; font-size: 16px; margin: 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header"><p class="brand-title">🏗️ IRON WORKS</p><p class="brand-subtitle">ROMAN_DEV | FULL PRICE ENGINE v9.9</p></div>', unsafe_allow_html=True)

# --- 2. ПАРСЕР ПОЛНОГО ПРАЙСА ---
@st.cache_data
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line: continue
                try:
                    # Убираем нумерацию "1:", "2:" и т.д.
                    clean_line = re.sub(r'^\d+:\s*', '', line)
                    parts = clean_line.split(",")
                    if len(parts) >= 3:
                        name = ",".join(parts[:-2]).strip()
                        weight = float(parts[-2].replace(",", ".").strip())
                        price = float(parts[-1].replace(",", ".").strip())
                        prices[name] = {"weight": weight, "price": price}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ИНТЕРФЕЙС ---
with st.sidebar:
    st.header("⚙️ ВВОД ДАННЫХ")
    if all_prices:
        mat_list = list(all_prices.keys())
        selected_mat = st.selectbox("ВЫБЕРИТЕ МАТЕРИАЛ:", options=mat_list)
        data = all_prices[selected_mat]
        
        is_sheet = "Лист" in selected_mat
        is_round = "круглая" in selected_mat.lower()
        
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: ЛИСТ")
            L_s, W_s = st.number_input("Лист Длина (мм)", 2500), st.number_input("Лист Ширина (мм)", 1250)
            L_d, W_d = st.number_input("Деталь Длина (мм)", 600), st.number_input("Деталь Ширина (мм)", 400)
            Qty = st.number_input("Кол-во шт", 1, 5000, 10)
        else:
            st.info("🏗️ РЕЖИМ: КАРКАС")
            L_f, W_f, H_f = st.number_input("L (мм)", 2000), st.number_input("W (мм)", 1000), st.number_input("H (мм)", 800)
            
            # Авто-поиск размеров сечения для малярки
            dims = re.findall(r'(\d+(?:\.\d+)?)', selected_mat)
            if is_round and dims:
                diam = float(dims[0])
                st.caption(f"Определен диаметр: {diam} мм")
            elif len(dims) >= 2:
                A_def, B_def = float(dims[0]), float(dims[1])
                A = st.number_input("Сторона A (мм)", value=int(A_def))
                B = st.number_input("Сторона B (мм)", value=int(B_def))
            else:
                A = st.number_input("Сторона A (мм)", 40)
                B = st.number_input("Сторона B (мм)", 20)

        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)

# --- 4. ЛОГИКА И ВЫВОД ---
if calc and all_prices:
    if not is_sheet:
        # --- ТРУБА ---
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        real_len = pure_len * 1.05
        weight_t = real_len * data['weight']
        cost_t = (weight_t * data['price']) * 1.10
        
        if is_round:
            paint_s = (math.pi * diam / 1000) * real_len
        else:
            paint_s = ((A + B) * 2 / 1000) * real_len

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{weight_t:.1f} кг")
        c2.metric("Метраж", f"{real_len:.1f} м")
        c3.metric("Малярка", f"{paint_s:.2f} м²")
        c4.metric("Смета", f"{cost_t:.0f} грн")

        # 3D
        x, y, z = [], [], []
        edges = [([0,L_f],[0,0],[0,0]), ([0,L_f],[W_f,W_f],[0,0]), ([0,L_f],[0,0],[H_f,H_f]), ([0,L_f],[W_f,W_f],[H_f,H_f]),
                 ([0,0],[0,W_f],[0,0]), ([L_f,L_f],[0,W_f],[0,0]), ([0,0],[0,W_f],[H_f,H_f]), ([L_f,L_f],[0,W_f],[H_f,H_f]),
                 ([0,0],[0,0],[0,H_f]), ([L_f,L_f],[0,0],[0,H_f]), ([0,0],[W_f,W_f],[0,H_f]), ([L_f,L_f],[W_f,W_f],[0,H_f])]
        for e in edges:
            x.extend([e[0][0], e[0][1], None]); y.extend([e[1][0], e[1][1], None]); z.extend([e[2][0], e[2][1], None])
        
        fig = go.Figure(data=go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), paper_bgcolor='#0e1117', height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🤖 nanoCAD")
        st.code(f"(defun c:IronFrame () (command \"_BOX\" '(0 0 0) \"_L\" {float(L_f)} {float(W_f)} {float(H_f)}) (princ))", language="lisp")

    else:
        # --- ЛИСТ ---
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        if on_sheet > 0:
            needed = -(-Qty // on_sheet)
            # Для листов в твоем прайсе цена за лист или за кг? 
            # В коде ниже считаем: Вес одного листа * Цена из прайса * Кол-во листов
            # (Если в прайсе цена за КГ - то убери деление на 1.0 в формуле цены)
            w_total = data['weight'] * needed
            c_total = w_total * data['price']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("На листе", f"{on_sheet} шт")
            c2.metric("Листов", f"{needed} шт")
            c3.metric("Вес/Цена", f"{w_total:.1f}кг / {c_total:.0f}грн")

            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=L_s, y1=W_s, line=dict(color="Cyan", width=3), fillcolor="rgba(0,200,255,0.1)")
            idx = 0
            for r in range(int(rows)):
                for c in range(int(cols)):
                    if idx < Qty:
                        fig.add_shape(type="rect", x0=c*L_d, y0=r*W_d, x1=(c+1)*L_d, y1=(r+1)*W_d, line=dict(color="White"), fillcolor="Orange")
                        idx += 1
            fig.update_layout(xaxis=dict(range=[-50, L_s+50]), yaxis=dict(range=[-50, W_s+50]), paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=500)
            st.plotly_chart(fig)
            
            st.code(f"(defun c:IronSheet () (command \"_RECTANG\" '(0 0) '({float(L_s)} {float(W_s)})) (princ))", language="lisp")
            