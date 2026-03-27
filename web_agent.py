import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ ИНТЕРФЕЙСА ---
st.set_page_config(page_title="IRON WORKS v13.4", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .price-details { background: #1b2b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; color: #ccffea; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ IRON WORKS | Full Engineering v13.4")

# --- 2. БРОНЕБОЙНЫЙ ПАРСЕР (v13.3+) ---
@st.cache_data
def load_db():
    catalog = {}
    if not os.path.exists("prices.txt"): return catalog
    with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line: continue
            try:
                clean_line = re.sub(r'^\d+:\s*', '', line)
                parts = clean_line.split(",")
                name = parts[0].strip()
                weight = float(parts[1].strip().replace(',', '.'))
                p_unit = float(parts[2].strip().replace(',', '.'))
                p_ton = float(parts[3].strip().replace(',', '.'))
                nums = re.findall(r'(\d+\.\d+|\d+)', name)
                thick = float(nums[-1]) if nums else 2.0
                catalog[name] = {"weight": weight, "p_unit": p_unit, "p_ton": p_ton, "thick": thick}
            except: continue
    return catalog

db = load_db()

# --- 3. ЛОГИКА СВАРКИ ---
def get_welding_advice(thick):
    if thick < 1.6:
        return {"crit": "ВЫСОКАЯ (Риск прожога)", "amp": "30-55A", "el": "1.6-2.0мм", "meth": "Точечно, с паузами для охлаждения. Контроль деформаций!"}
    elif 1.6 <= thick < 3.0:
        return {"crit": "СРЕДНЯЯ", "amp": "65-95A", "el": "2.5-3.0мм", "meth": "Прерывистый шов или «вразброс» для минимизации потяжек."}
    else:
        return {"crit": "НИЗКАЯ (Стабильный провар)", "amp": "100-145A", "el": "3.0-4.0мм", "meth": "Сплошной шов. Свыше 4мм — обязательная разделка кромок."}

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
if not db:
    st.error("Файл prices.txt не найден или пуст! Проверь формат с номировкой.")
else:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Выбор металла:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        
        mode = st.radio("Расценка:", ["Розница (м.п./шт)", "Опт (Тонна)"])
        
        if is_sheet:
            L, W = st.number_input("Лист L (мм)", 2500.0), st.number_input("Лист W (мм)", 1250.0)
            dl, dw = st.number_input("Деталь l (мм)", 600.0), st.number_input("Деталь w (мм)", 400.0)
            qty = st.number_input("Количество (шт)", 1, 1000, 10)
        else:
            rl, rw, rh = st.number_input("Длина (мм)", 2000.0), st.number_input("Ширина (мм)", 1000.0), st.number_input("Высота (мм)", 1200.0)
            stock = st.number_input("Длина палки (м)", 6.0)
            
        markup = st.slider("Наценка на расходники %", 0, 100, 15)
        calc_btn = st.button("🚀 ВЫПОЛНИТЬ РАСЧЕТ", use_container_width=True)

    # --- 5. ГЛАВНЫЙ БЛОК РАСЧЕТА ---
    if calc_btn:
        weld = get_welding_advice(item['thick'])
        
        if is_sheet:
            on_sheet = max(1, (L // dl) * (W // dw))
            needed = -(-qty // on_sheet)
            weight_buy = needed * item['weight']
            base = (needed * item['p_unit']) if "Розница" in mode else (weight_buy/1000 * item['p_ton'])
            waste = ((needed * L * W - qty * dl * dw) / (needed * L * W)) * 100
            unit_label = "листов"
            count_val = needed
        else:
            m_clear = (rl*4 + rw*4 + rh*4) / 1000
            sticks = -(-m_clear // max(0.1, stock))
            total_m = sticks * stock
            weight_buy = total_m * item['weight']
            base = (total_m * item['p_unit']) if "Розница" in mode else (weight_buy/1000 * item['p_ton'])
            waste = ((total_m - m_clear) / total_m) * 100
            unit_label = "палок"
            count_val = sticks

        total_price = base * (1 + markup/100)

        # ВЫВОД МЕТРИК
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(count_val)} {unit_label}")
        c2.metric("Вес", f"{weight_buy:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # БЛОК ДЕТАЛИЗАЦИИ ЦЕНЫ
        st.markdown(f"""
        <div class="price-details">
            💰 <b>Детализация сметы:</b><br>
            Металл: {base:.2f} грн | Наценка: {markup}% (+{base * markup/100:.2f} грн)<br>
            Итоговая стоимость заказа: <b>{total_price:.2f} грн</b>
        </div>
        """, unsafe_allow_html=True)

        # БЛОК ИНЖЕНЕРНЫХ ПОДСКАЗОК
        st.subheader("🛠️ Инженерный отдел")
        st.markdown(f"""
        <div class="eng-card">
            <b>МАТЕРИАЛ:</b> {sel} (Толщина: {item['thick']}мм)<br>
            <b>СЛОЖНОСТЬ СВАРКИ:</b> {weld['crit']}<br>
            <b>ТОК:</b> {weld['amp']} | <b>ЭЛЕКТРОД:</b> {weld['el']}<br>
            <b>МЕТОД:</b> {weld['meth']}
        </div>
        """, unsafe_allow_html=True)
        
        if waste > 20:
            st.markdown(f'<div class="waste-card">⚠️ <b>ВНИМАНИЕ:</b> Высокий процент отхода ({waste:.1f}%). Рекомендуется проверить кратность раскроя деталей под размер листа/трубы.</div>', unsafe_allow_html=True)

        # 3D МОДЕЛЬ
        fig = go.Figure()
        x = [0, (L if is_sheet else rl), (L if is_sheet else rl), 0, 0,  0, (L if is_sheet else rl), (L if is_sheet else rl), 0, 0, None, (L if is_sheet else rl), (L if is_sheet else rl), None, 0, 0]
        y = [0, 0, (W if is_sheet else rw), (W if is_sheet else rw), 0,  0, 0, (W if is_sheet else rw), (W if is_sheet else rw), 0, None, 0, 0, None, (W if is_sheet else rw), (W if is_sheet else rw)]
        z = [0, 0, 0, 0, 0, (item['thick'] if is_sheet else rh), (item['thick'] if is_sheet else rh), (item['thick'] if is_sheet else rh), (item['thick'] if is_sheet else rh), (item['thick'] if is_sheet else rh), None, 0, (item['thick'] if is_sheet else rh), None, 0, (item['thick'] if is_sheet else rh)]
        
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=6), name="Конструкция"))
        fig.update_layout(scene=dict(aspectmode='data'), height=550, margin=dict(l=0,r=0,b=0,t=0), paper_bgcolor='#0e1117')
        st.plotly_chart(fig, use_container_width=True)

        # CAD ЭКСПОРТ
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {L if is_sheet else rl} {W if is_sheet else rw} {item['thick'] if is_sheet else rh}) (princ))")
        