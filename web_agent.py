import streamlit as st
import os
import plotly.graph_objects as go
import re
import math

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v10.7", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin: 15px 0; color: #e0f4ff; }
    .ok-card { border-left: 6px solid #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | PAINT & 3D ENGINE v10.7</p></div>', unsafe_allow_html=True)

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
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    prices[name] = {"weight": weight, "price": price, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ГЕОМЕТРИЯ 3D ---
def get_clean_box_coords(x0, y0, z0, l, w, h):
    x, y, z = [], [], []
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0, z0, z0, z0, z0, None]
    x += [x0, x0+l, x0+l, x0, x0, None]
    y += [y0, y0, y0+w, y0+w, y0, None]
    z += [z0+h, z0+h, z0+h, z0+h, z0+h, None]
    for dx, dy in [(0,0), (l,0), (l,w), (0,w)]:
        x += [x0+dx, x0+dx, None]; y += [y0+dy, y0+dy, None]; z += [z0, z0+h, None]
    return x, y, z

# --- 4. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        selected_mat = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        is_round = "круглая" in selected_mat.lower()
        st.divider()
        if is_sheet:
            L_s, W_s = st.number_input("Лист L", value=2500), st.number_input("Лист W", value=1250)
            L_d, W_d = st.number_input("Деталь l", value=600), st.number_input("Деталь w", value=400)
            Qty = st.number_input("Кол-во деталей", value=10, min_value=1)
        else:
            L_f, W_f, H_f = st.number_input("Длина L", value=2000), st.number_input("Ширина W", value=1000), st.number_input("Высота H", value=1200)
            # Извлекаем размеры сечения для малярки
            dims = re.findall(r'(\d+)', selected_mat)
            if is_round and dims: diam = float(dims[0])
            elif len(dims) >= 2: A, B = float(dims[0]), float(dims[1])
            else: A, B = 40.0, 20.0
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 5. РАСЧЕТ ---
if calc and all_prices:
    thick = data['thick']
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 0
        paint_area = (L_s * W_s * 2 / 1_000_000) * needed # Две стороны листа в м2
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("На листе", f"{on_sheet} шт"); c2.metric("Листов", f"{needed} шт")
        c3.metric("Вес", f"{(data['weight']*needed):.1f} кг"); c4.metric("Малярка", f"{paint_area:.2f} м²")
        
        fig = go.Figure()
        xl, yl, zl = get_clean_box_coords(0, 0, 0, L_s, W_s, thick)
        fig.add_trace(go.Scatter3d(x=xl, y=yl, z=zl, mode='lines', line=dict(color='cyan', width=4), name="Лист"))
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    xd, yd, zd = get_clean_box_coords(c*L_d, r*W_d, thick, L_d, W_d, thick/2)
                    fig.add_trace(go.Scatter3d(x=xd, y=yd, z=zd, mode='lines', line=dict(color='orange', width=2)))
                    idx += 1
        st.plotly_chart(fig, use_container_width=True)
    else:
        m_pure = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        m_real = m_pure * 1.05
        w_total = m_real * data['weight']
        # Расчет площади покраски трубы
        if is_round: paint_area = (math.pi * diam / 1000) * m_real
        else: paint_area = ((A + B) * 2 / 1000) * m_real
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{w_total:.1f} кг"); c2.metric("Метраж", f"{m_real:.1f} м")
        c3.metric("Малярка", f"{paint_area:.2f} м²"); c4.metric("Смета", f"{(w_total*data['price']*1.1):.0f} грн")
        
        xf, yf, zf = get_clean_box_coords(0, 0, 0, L_f, W_f, H_f)
        fig = go.Figure(data=go.Scatter3d(x=xf, y=yf, z=zf, mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), height=600, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

    # ИНЖЕНЕРКА
    st.subheader("🛡️ Инженерное заключение")
    is_crit = thick < 2.0
    st.markdown(f"""<div class="eng-card {' ' if is_crit else 'ok-card'}">
        <b>Толщина металла: {thick} мм</b> | <b>Риск деформации:</b> {"ВЫСОКИЙ" if is_crit else "НИЗКИЙ"}<br>
        🛠️ <b>Метод:</b> {"Прихватки, малый ток, шахматный порядок" if is_crit else "Сплошной шов"}<br>
        🎨 <b>Малярка:</b> {paint_area:.2f} м² (рекомендуется грунт-эмаль 3-в-1).
    </div>""", unsafe_allow_html=True)
    