import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v12.2", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background-color: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .crit-high { border-left-color: #ff4b4b; }
    .crit-low { border-left-color: #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | FULL ESTIMATE v12.2</p></div>', unsafe_allow_html=True)

# --- 2. ЛОГИКА СВАРКИ ---
def get_welding_advice(thick):
    if thick < 1.5:
        return {"crit": "ВЫСОКАЯ (Риск прожога)", "amp": "30-50A", "el": "1.6-2.0мм", "meth": "Точечно, с паузами.", "cls": "crit-high"}
    elif 1.5 <= thick < 3.0:
        return {"crit": "СРЕДНЯЯ (Контроль деформаций)", "amp": "60-90A", "el": "2.5-3.0мм", "meth": "Прерывистый шов.", "cls": ""}
    else:
        return {"crit": "НИЗКАЯ (Стабильный провар)", "amp": "100-140A", "el": "3.0-4.0мм", "meth": "Сплошной шов.", "cls": "crit-low"}

# --- 3. ПАРСЕР ---
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

# --- 4. ГЕОМЕТРИЯ ---
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

# --- 5. PDF ---
def generate_pdf_bytes(res, weld):
    pdf = FPDF()
    pdf.add_page()
    f_p = "arial.ttf"
    if os.path.exists(f_p):
        pdf.add_font('Arial', '', f_p); pdf.set_font('Arial', '', 14)
    else:
        pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=f"СМЕТА И ТЕХ-КАРТА: {res['name']}", ln=True, align='C')
    pdf.ln(5)
    for k, v in res['metrics'].items():
        pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 8, txt=f"СВАРКА: {weld['crit']}. Ток: {weld['amp']}. Метод: {weld['meth']}")
    return bytes(pdf.output())

# --- 6. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        sel = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[sel]
        is_sheet = "Лист" in sel
        st.divider()
        if is_sheet:
            Ls, Ws = st.number_input("Лист L", 2500), st.number_input("Лист W", 1250)
            Ld, Wd = st.number_input("Деталь l", 600), st.number_input("Деталь w", 400)
            Qty = st.number_input("Кол-во", 10, 1)
        else:
            Lf, Wf, Hf = st.number_input("L", 2000), st.number_input("W", 1000), st.number_input("H", 1200)
            stock_m = st.number_input("Длина палки (м)", 6.0)
        calc = st.button("🚀 РАССЧИТАТЬ СМЕТУ", use_container_width=True)

# --- 7. ОСНОВНОЙ РАСЧЕТ ---
if calc and all_prices:
    thick = data['thick']
    weld = get_welding_advice(thick)
    report = {"name": sel, "metrics": {}}
    
    if is_sheet:
        on_sheet = (Ls // Ld) * (Ws // Wd)
        needed = -(-Qty // on_sheet) if on_sheet > 0 else 1
        w_buy = data['weight'] * needed
        w_clear = (Ld * Wd * Qty / (Ls * Ws)) * w_buy
        waste = ((w_buy - w_clear) / w_buy) * 100
        total_cost = w_buy * data['price'] * 1.1 # +10% расходники
        
        report["metrics"] = {"Листов": needed, "Вес закупки": f"{w_buy:.1f}кг", "Чистый вес": f"{w_clear:.1f}кг", "Отход": f"{waste:.1f}%", "СМЕТА": f"{total_cost:.0f} грн"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{w_buy:.1f} кг")
        c2.metric("Чистый вес", f"{w_clear:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%", delta=f"{w_buy-w_clear:.1f} кг", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_cost:.0f}")
    else:
        m_total = (Lf*4 + Wf*4 + Hf*4) / 1000
        needed_p = -(-m_total // stock_m)
        w_buy = needed_p * stock_m * data['weight']
        w_clear = m_total * data['weight']
        waste = ((w_buy - w_clear) / w_buy) * 100
        total_cost = w_buy * data['price'] * 1.1
        
        report["metrics"] = {"Палки (шт)": needed_p, "Метраж чистый": f"{m_total:.2f}м", "Вес закупки": f"{w_buy:.1f}кг", "Отход": f"{waste:.1f}%", "СМЕТА": f"{total_cost:.0f} грн"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{w_buy:.1f} кг")
        c2.metric("Метраж", f"{m_total:.1f} м")
        c3.metric("Отход", f"{waste:.1f}%", delta=f"{(needed_p*stock_m)-m_total:.1f} м", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_cost:.0f}")

    # БЛОК ИНЖЕНЕРА
    if waste > 20:
        st.markdown(f'<div class="waste-card">⚠️ Высокий отход металла! ({waste:.1f}%)</div>', unsafe_allow_html=True)

    st.subheader("🛡️ Инженерно-сварочная карта")
    st.markdown(f"""
    <div class="eng-card {weld['cls']}">
        <b>Критичность:</b> {weld['crit']} | <b>Метод:</b> {weld['meth']}<br>
        <b>Ток:</b> {weld['amp']} | <b>Электрод:</b> {weld['el']}
    </div>
    """, unsafe_allow_html=True)

    # 3D И ЭКСПОРТ
    fig = go.Figure()
    x, y, z = get_clean_box_coords(0,0,0, Ls if is_sheet else Lf, Ws if is_sheet else Wf, thick if is_sheet else Hf)
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=5)))
    fig.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a: st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {Ls if is_sheet else Lf} {Ws if is_sheet else Wf} {thick if is_sheet else Hf}) (princ))", language="lisp")
    with col_b: st.download_button("📥 СКАЧАТЬ ПОЛНУЮ СМЕТУ (PDF)", data=generate_pdf_bytes(report, weld), file_name="iron_estimate.pdf")
    