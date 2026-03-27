import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v12.4", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .price-card { background-color: #1b2b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; color: #ccffea; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | PRECISION PRICE v12.4</p></div>', unsafe_allow_html=True)

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
                    price_per_kg = float(parts[-1].replace(",", "."))
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    prices[name] = {"weight_unit": weight, "price_kg": price_per_kg, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ГЕОМЕТРИЯ ---
def get_clean_box_coords(x0, y0, z0, l, w, h):
    x, y, z = [], [], []
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0, z0, z0, z0, z0, None]
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0+0, y0+0, y0+w, y0+w, y0, None]
    z += [z0+h, z0+h, z0+h, z0+h, z0+h, None]
    for dx, dy in [(0,0), (l,0), (l,w), (0,w)]:
        x += [x0+dx, x0+dx, None]; y += [y0+dy, y0+dy, None]; z += [z0, z0+h, None]
    return x, y, z

# --- 4. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        sel = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[sel]
        is_sheet = "Лист" in sel
        st.divider()
        if is_sheet:
            Ls = st.number_input("Лист L (мм)", value=2500.0)
            Ws = st.number_input("Лист W (мм)", value=1250.0)
            Ld = st.number_input("Деталь l (мм)", value=600.0)
            Wd = st.number_input("Деталь w (мм)", value=400.0)
            Qty = st.number_input("Количество (шт)", value=10, min_value=1)
        else:
            Lf = st.number_input("Рама L (мм)", value=2000.0)
            Wf = st.number_input("Рама W (мм)", value=1000.0)
            Hf = st.number_input("Рама H (мм)", value=1200.0)
            stock_m = st.number_input("Длина трубы (м)", value=6.0)
        
        markup = st.slider("Наценка на расходники %", 0, 30, 10)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 5. РАСЧЕТ ---
if calc and all_prices:
    thick = data['thick']
    price_kg = data['price_kg']
    
    if is_sheet:
        # Считаем сколько штук в ОДНОМ листе
        on_sheet = max(1, (Ls // Ld) * (Ws // Wd))
        # Сколько листов нужно купить
        needed_sheets = -(-Qty // on_sheet)
        
        # Вес одного листа (исходим из того, что в базе вес за 1 м2 или за лист)
        # Для точности считаем вес через площадь, если в базе вес за м2
        area_one_sheet = (Ls * Ws) / 1_000_000
        # Если в базе вес указан за м2 (обычно для листов так), умножаем. 
        # Если вес за целый лист - используем как есть.
        weight_of_all_sheets = data['weight_unit'] * needed_sheets
        
        cost_metal = weight_of_all_sheets * price_kg
        total_cost = cost_metal * (1 + markup/100)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Нужно листов", int(needed_sheets))
        c2.metric("Вес закупки", f"{weight_of_all_sheets:.1f} кг")
        c3.metric("Цена металла", f"{cost_metal:.0f} грн")
        c4.metric("ИТОГО (с допами)", f"{total_cost:.0f} грн")
        
        st.markdown(f'<div class="price-card">💰 <b>Детализация:</b> {needed_sheets} лист(а) по {data["weight_unit"]}кг. Цена: {price_kg} грн/кг.</div>', unsafe_allow_html=True)
        
    else:
        m_total = (Lf*4 + Wf*4 + Hf*4) / 1000
        needed_sticks = -(-m_total // max(0.1, stock_m))
        weight_buy = needed_sticks * stock_m * data['weight_unit']
        
        cost_metal = weight_buy * price_kg
        total_cost = cost_metal * (1 + markup/100)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Целых палок", int(needed_sticks))
        c2.metric("Вес закупки", f"{weight_buy:.1f} кг")
        c3.metric("Цена металла", f"{cost_metal:.0f} грн")
        c4.metric("ИТОГО (с допами)", f"{total_cost:.0f} грн")

    # 3D ПРЕДОСМОТР
    fig = go.Figure()
    x, y, z = get_clean_box_coords(0,0,0, Ls if is_sheet else Lf, Ws if is_sheet else Wf, thick if is_sheet else Hf)
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=5)))
    fig.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    # КОД ДЛЯ NANOCAD
    st.subheader("🤖 Код для nanoCAD")
    st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {Ls if is_sheet else Lf} {Ws if is_sheet else Wf} {thick if is_sheet else Hf}) (princ))", language="lisp")
    