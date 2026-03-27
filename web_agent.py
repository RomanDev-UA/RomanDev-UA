import streamlit as st
import os
import plotly.graph_objects as go

# --- 1. КОСМЕТИКА ---
st.set_page_config(page_title="IRON WORKS v9.5", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .brand-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px; }
    .brand-title { color: white !important; font-size: 42px; font-weight: 900; margin: 0; }
    .brand-subtitle { color: #00c6ff !important; font-size: 16px; margin: 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header"><p class="brand-title">🏗️ IRON WORKS</p><p class="brand-subtitle">ROMAN_DEV | CAD AUTOMATION v9.5</p></div>', unsafe_allow_html=True)

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
    return f"(defun c:IronFrame () (setq p1 '(0 0 0)) (command \"_BOX\" p1 \"_L\" {l} {w} {h}) (princ \"\\nКаркас готов.\") (princ))"

def generate_sheet_lisp(ls, ws, ld, wd, cols, rows, qty):
    # Рисуем лист и сетку деталей
    lisp = f"(defun c:IronSheet () (command \"_RECTANG\" '(0 0) '({ls} {ws})) "
    count = 0
    for r in range(int(rows)):
        for c in range(int(cols)):
            if count < qty:
                x1, y1 = c * ld, r * wd
                x2, y2 = (c + 1) * ld, (r + 1) * wd
                lisp += f"(command \"_RECTANG\" '({x1} {y1}) '({x2} {y2})) "
                count += 1
    lisp += "(princ \"\\nРаскрой листа готов.\") (princ))"
    return lisp

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        mat_name = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[mat_name]
        is_sheet = "Лист" in mat_name or "Лист" in mat_name.capitalize()
        
        if is_sheet:
            st.success("📦 РЕЖИМ: ЛИСТ")
            L_s, W_s = st.number_input("Лист Длина", 2500), st.number_input("Лист Ширина", 1250)
            L_d, W_d = st.number_input("Деталь Длина", 600), st.number_input("Деталь Ширина", 400)
            Qty = st.number_input("Кол-во шт", 10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: КАРКАС")
            L_f, W_f, H_f = st.number_input("L (мм)", 2000), st.number_input("W (мм)", 1000), st.number_input("H (мм)", 1200)
            Prof_A, Prof_B = st.number_input("Профиль А", 40), st.number_input("Профиль Б", 20)
        
        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)

# --- 5. РЕЗУЛЬТАТ ---
if calc and all_prices:
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        if on_sheet > 0:
            needed = -(-Qty // on_sheet)
            st.metric("Листов нужно", f"{needed} шт", f"По {on_sheet} на листе")
            
            # График
            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=L_s, y1=W_s, line=dict(color="Cyan"), fillcolor="rgba(0,100,255,0.2)")
            c_idx = 0
            for r in range(int(rows)):
                for c in range(int(cols)):
                    if c_idx < Qty:
                        fig.add_shape(type="rect", x0=c*L_d, y0=r*W_d, x1=(c+1)*L_d, y1=(r+1)*W_d, line=dict(color="White"), fillcolor="Orange")
                        c_idx += 1
            fig.update_layout(xaxis=dict(range=[-100, L_s+100]), yaxis=dict(range=[-100, W_s+100]), paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=500)
            st.plotly_chart(fig)
            
            # LISP Код
            st.subheader("🤖 Код для nanoCAD (Раскрой)")
            lisp_txt = generate_sheet_lisp(L_s, W_s, L_d, W_d, cols, rows, Qty)
            st.code(lisp_txt, language="lisp")
            st.info("Команда в nanoCAD: IronSheet")
    else:
        # Тут 3D Каркас (Plotly) и его Lisp (IronFrame)
        # (Код 3D из v9.3 оставляем без изменений)
        st.write("Рисуем 3D...")
        