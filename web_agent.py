import streamlit as st
import os
import plotly.graph_objects as go
import re
import math

# --- 1. СТИЛИ И ИНТЕРФЕЙС ---
st.set_page_config(page_title="IRON WORKS v10.4", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin: 15px 0; color: #e0f4ff; }
    .ok-card { border-left: 6px solid #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | ENGINEERING & 3D NESTING v10.4</p></div>', unsafe_allow_html=True)

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
                    # Поиск толщины (ищем число перед запятой или в названии)
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    prices[name] = {"weight": weight, "price": price, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ФУНКЦИИ ГЕНЕРАЦИИ 3D ---
def get_box_coords(x0, y0, z0, l, w, h):
    x = [x0, x0+l, x0+l, x0, x0, x0, x0+l, x0+l, x0, x0, x0+l, x0+l, x0+l, x0+l, x0, x0]
    y = [y0, y0, y0+w, y0+w, y0, y0, y0, y0+w, y0+w, y0, y0+w, y0+w, y0+w, y0+w, y0+y0, y0] # Исправлено y0
    y = [y0, y0, y0+w, y0+w, y0, y0, y0, y0+w, y0+w, y0, y0+w, y0+w, y0+w, y0+w, y0, y0]
    z = [z0, z0, z0, z0, z0, z0+h, z0+h, z0+h, z0+h, z0+h, z0+h, z0, z0, z0+h, z0+h, z0]
    return x, y, z

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        selected_mat = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[selected_mat]
        is_sheet = "Лист" in selected_mat
        st.divider()
        if is_sheet:
            L_s, W_s = st.number_input("Лист L", 2500), st.number_input("Лист W", 1250)
            L_d, W_d = st.number_input("Деталь l", 600), st.number_input("Деталь w", 400)
            Qty = st.number_input("Кол-во шт", 1, 1000, 10)
        else:
            L_f, W_f, H_f = st.number_input("Длина L", 2000), st.number_input("Ширина W", 1000), st.number_input("Высота H", 1200)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 5. ОСНОВНОЙ БЛОК ---
if calc and all_prices:
    thick = data['thick']
    
    if is_sheet:
        cols, rows = L_s // L_d, W_s // W_d
        on_sheet = int(cols * rows)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 0
        
        st.subheader("📋 Результаты раскроя")
        c1, c2, c3 = st.columns(3)
        c1.metric("На листе", f"{on_sheet} шт")
        c2.metric("Листов", f"{needed} шт")
        c3.metric("Вес", f"{(data['weight']*needed):.1f} кг")

        # 3D НЕСТИНГ
        fig = go.Figure()
        # Лист
        xl, yl, zl = get_box_coords(0,0,0, L_s, W_s, thick)
        fig.add_trace(go.Scatter3d(x=xl, y=yl, z=zl, mode='lines', line=dict(color='cyan', width=4), name="Лист"))
        # Детали
        idx = 0
        for r in range(int(rows)):
            for c in range(int(cols)):
                if idx < Qty:
                    xd, yd, zd = get_box_coords(c*L_d, r*W_d, thick, L_d, W_d, thick/2)
                    fig.add_trace(go.Scatter3d(x=xd, y=yd, z=zd, mode='lines', line=dict(color='orange', width=2), name=f"Дет.{idx+1}"))
                    idx += 1
        fig.update_layout(scene=dict(aspectmode='data'), height=600, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

    else:
        # ТРУБЫ
        pure_m = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        w_total = pure_m * 1.05 * data['weight']
        cost = (w_total * data['price']) * 1.10
        
        st.subheader("🏗️ Параметры каркаса")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{w_total:.1f} кг"); c2.metric("Метраж", f"{pure_m:.1f} м")
        c3.metric("Малярка", f"{(pure_m*0.15):.2f} м²"); c4.metric("Смета", f"{cost:.0f} грн")

        # 3D КАРКАС
        xf, yf, zf = get_box_coords(0,0,0, L_f, W_f, H_f)
        fig = go.Figure(data=go.Scatter3d(x=xf, y=yf, z=zf, mode='lines', line=dict(color='#00c6ff', width=8)))
        fig.update_layout(scene=dict(aspectmode='data'), height=600, paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

    # --- ИНЖЕНЕРНЫЙ БЛОК (ПРАВКИ ПО ДЕФОРМАЦИИ И СВАРКЕ) ---
    st.subheader("🛡️ Инженерное заключение")
    is_crit = thick < 2.0
    card_style = "eng-card" if is_crit else "eng-card ok-card"
    
    risk_text = "КРИТИЧЕСКИЙ (Тонкий металл)" if is_crit else "НИЗКИЙ (Стабильный металл)"
    method = "Сварка точками / в разбежку / малый ток" if is_crit else "Сплошной шов / ток 100-130А"
    
    st.markdown(f"""
    <div class="{card_style}">
        <b>Толщина металла: {thick} мм</b><br>
        🔥 <b>Риск деформации:</b> {risk_text}<br>
        🛠️ <b>Метод сварки:</b> {method}<br>
        ⚠️ <b>Рекомендация:</b> {"Используйте теплоотвод и зажимы, чтобы не покрутило!" if is_crit else "Проверьте катет шва на соответствие чертежу."}
    </div>
    """, unsafe_allow_html=True)
    
    st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L_s if is_sheet else L_f} {W_s if is_sheet else W_f} {thick if is_sheet else H_f}) (princ))", language="lisp")
    