import streamlit as st
import os
import plotly.graph_objects as go

# --- 1. КОСМЕТИКА ---
st.set_page_config(page_title="IRON WORKS v9.4", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .brand-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px; }
    .brand-title { color: white !important; font-size: 42px; font-weight: 900; margin: 0; }
    .brand-subtitle { color: #00c6ff !important; font-size: 16px; margin: 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header"><p class="brand-title">🏗️ IRON WORKS</p><p class="brand-subtitle">ROMAN_DEV | SHEET CUTTING ENGINE v9.4</p></div>', unsafe_allow_html=True)

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

# --- 3. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ НАСТРОЙКИ")
    if all_prices:
        mat_name = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[mat_name]
        is_sheet = "Лист" in mat_name or "Лист" in mat_name.capitalize()
        
        if is_sheet:
            st.success("📦 РЕЖИМ: РАСКРОЙ ЛИСТА")
            L_s = st.number_input("Длина листа (мм)", value=2500)
            W_s = st.number_input("Ширина листа (мм)", value=1250)
            st.divider()
            L_d = st.number_input("Длина детали (мм)", value=600)
            W_d = st.number_input("Ширина детали (мм)", value=400)
            Qty = st.number_input("Кол-во деталей (шт)", value=10, min_value=1)
        else:
            st.info("🏗️ РЕЖИМ: КАРКАС")
            L_f = st.number_input("Длина L (мм)", value=2000)
            W_f = st.number_input("Ширина W (мм)", value=1000)
            H_f = st.number_input("Высота H (мм)", value=1200)
        
        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)

# --- 4. РАСЧЕТ И ВИЗУАЛИЗАЦИЯ ---
if calc and all_prices:
    if is_sheet:
        # Простая логика раскроя (рядами)
        cols = L_s // L_d
        rows = W_s // W_d
        on_sheet = int(cols * rows)
        
        if on_sheet == 0:
            st.error("Деталь больше листа!")
        else:
            needed_sheets = -(-Qty // on_sheet) # Округление вверх
            total_weight = (L_s * W_s / 1000000) * sel['weight'] * needed_sheets
            total_cost = total_weight * sel['price']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("На листе", f"{on_sheet} шт")
            c2.metric("Всего листов", f"{needed_sheets} шт")
            c3.metric("Вес / Цена", f"{total_weight:.1f}кг / {total_cost:.0f}грн")

            # Визуализация раскроя
            st.subheader("📋 Схема раскладки на одном листе")
            fig = go.Figure()
            # Лист
            fig.add_shape(type="rect", x0=0, y0=0, x1=L_s, y1=W_s, line=dict(color="RoyalBlue", width=3), fillcolor="LightSkyBlue", opacity=0.2)
            
            # Детали
            count = 0
            for r in range(int(rows)):
                for c in range(int(cols)):
                    if count < Qty:
                        fig.add_shape(type="rect", x0=c*L_d, y0=r*W_d, x1=(c+1)*L_d, y1=(r+1)*W_d, line=dict(color="White", width=1), fillcolor="Orange")
                        count += 1
            
            fig.update_layout(xaxis=dict(range=[-100, L_s+100]), yaxis=dict(range=[-100, W_s+100]), width=800, height=450, paper_bgcolor='#0e1117', plot_bgcolor='#0e1117')
            st.plotly_chart(fig)
    else:
        # (Тут остается твой код 3D каркаса из v9.3)
        st.write("Тут твой 3D каркас...")
        