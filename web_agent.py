import streamlit as st
import os
import plotly.graph_objects as go

# --- 1. КОСМЕТИКА ---
st.set_page_config(page_title="IRON WORKS v9.6", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .brand-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px; }
    .brand-title { color: white !important; font-size: 42px; font-weight: 900; margin: 0; font-family: sans-serif; }
    .brand-subtitle { color: #00c6ff !important; font-size: 16px; margin: 0; font-family: sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header"><p class="brand-title">🏗️ IRON WORKS</p><p class="brand-subtitle">ROMAN_DEV | ALL-IN-ONE ENGINE v9.6</p></div>', unsafe_allow_html=True)

# --- 2. БАЗА ---
@st.cache_data
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "," not in line: continue
                try:
                    parts = line.strip().split(",")
                    name = ",".join(parts[:-2]).strip()
                    prices[name] = {"weight": float(parts[-2].replace(",", ".")), "price": float(parts[-1].replace(",", "."))}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ФУНКЦИИ LISP ---
def generate_frame_lisp(l, w, h):
    return f"(defun c:IronFrame () (setq p1 '(0 0 0)) (command \"_BOX\" p1 \"_L\" {float(l)} {float(w)} {float(h)}) (princ \"\\nКаркас отрисован.\") (princ))"

def generate_sheet_lisp(ls, ws, ld, wd, cols, rows, qty):
    lisp = f"(defun c:IronSheet () (command \"_RECTANG\" '(0 0) '({float(ls)} {float(ws)})) "
    count = 0
    for r in range(int(rows)):
        for c in range(int(cols)):
            if count < qty:
                x1, y1 = c * ld, r * wd
                x2, y2 = (c + 1) * ld, (r + 1) * wd
                lisp += f"(command \"_RECTANG\" '({float(x1)} {float(y1)}) '({float(x2)} {float(y2)})) "
                count += 1
    lisp += "(princ \"\\nРаскрой готов.\") (princ))"
    return lisp

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        mat_name = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[mat_name]
        is_sheet = "Лист" in mat_name or "Лист" in mat_name.capitalize()
        
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: ЛИСТ")
            L_s = st.number_input("Лист Длина (мм)", value=2500)
            W_s = st.number_input("Лист Ширина (мм)", value=1250)
            L_d = st.number_input("Деталь Длина (мм)", value=600)
            W_d = st.number_input("Деталь Ширина (мм)", value=400)
            Qty = st.number_input("Кол-во деталей (шт)", value=10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: ТРУБА / КАРКАС")
            L_f = st.number_input("Длина L (мм)", value=2500)
            W_f = st.number_input("Ширина W (мм)", value=1200)
            H_f = st.number_input("Высота H (мм)", value=1000)
            Prof_A = st.number_input("Профиль А (мм)", value=40)
            Prof_B = st.number_input("Профиль Б (мм)", value=20)
        
        st.divider()
        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)

# --- 5. РЕЗУЛЬТАТЫ ---
if calc and all_prices:
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        if on_sheet > 0:
            needed = -(-Qty // on_sheet)
            weight = (L_s * W_s / 1000000) * sel['weight'] * needed
            cost = weight * sel['price']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("На листе", f"{on_sheet} шт")
            c2.metric("Нужно листов", f"{needed} шт")
            c3.metric("Вес/Цена", f"{weight:.1f}кг / {cost:.0f}грн")

            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=L_s, y1=W_s, line=dict(color="Cyan", width=2))
            idx = 0
            for r in range(int(rows)):
                for c in range(int(cols)):
                    if idx < Qty:
                        fig.add_shape(type="rect", x0=c*L_d, y0=r*W_d, x1=(c+1)*L_d, y1=(r+1)*W_d, line=dict(color="White"), fillcolor="Orange")
                        idx += 1
            fig.update_layout(scene=dict(aspectmode='data'), paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=500)
            st.plotly_chart(fig)
            
            st.code(generate_sheet_lisp(L_s, W_s, L_d, W_d, cols, rows, Qty), language="lisp")
    else:
        # --- РЕЖИМ ТРУБЫ (3D КАРКАС) ---
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        total_len = pure_len * 1.05
        weight_t = total_len * sel['weight']
        cost_t = (weight_t * sel['price']) * 1.10
        paint = ((Prof_A + Prof_B) * 2 / 1000) * total_len

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{weight_t:.1f} кг")
        c2.metric("Метраж", f"{total_len:.1f} м")
        c3.metric("Малярка", f"{paint:.2f} м²")
        c4.metric("Цена", f"{cost_t:.0f} грн")

        # 3D Plotly
        x_lines, y_lines, z_lines = [], [], []
        edges = [([0, L_f], [0, 0], [0, 0]), ([0, L_f], [W_f, W_f], [0, 0]), ([0, L_f], [0, 0], [H_f, H_f]), ([0, L_f], [W_f, W_f], [H_f, H_f]),
                 ([0, 0], [0, W_f], [0, 0]), ([L_f, L_f], [0, W_f], [0, 0]), ([0, 0], [0, W_f], [H_f, H_f]), ([L_f, L_f], [0, W_f], [H_f, H_f]),
                 ([0, 0], [0, 0], [0, H_f]), ([L_f, L_f], [0, 0], [0, H_f]), ([0, 0], [W_f, W_f], [0, H_f]), ([L_f, L_f], [W_f, W_f], [0, H_f])]
        for e in edges:
            x_lines.extend([e[0][0], e[0][1], None]); y_lines.extend([e[1][0], e[1][1], None]); z_lines.extend([e[2][0], e[2][1], None])
            
        fig = go.Figure(data=go.Scatter3d(x=x_lines, y=y_lines, z=z_lines, mode='lines', line=dict(color='#00c6ff', width=6)))
        fig.update_layout(scene=dict(aspectmode='data'), paper_bgcolor='#0e1117', height=600)
        st.plotly_chart(fig)
        
        st.code(generate_frame_lisp(L_f, W_f, H_f), language="lisp")
        