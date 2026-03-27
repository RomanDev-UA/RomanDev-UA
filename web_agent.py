import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ И СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v12.5", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background-color: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .crit-high { border-left-color: #ff4b4b; }
    .crit-low { border-left-color: #00ffcc; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | FULL ENGINEER v12.5</p></div>', unsafe_allow_html=True)

# --- 2. ЛОГИКА СВАРКИ ---
def get_welding_advice(thick):
    if thick < 1.5:
        return {"crit": "ВЫСОКАЯ (Риск прожога)", "amp": "30-50A", "el": "1.6-2.0мм", "meth": "Точечно, с паузами для охлаждения.", "cls": "crit-high"}
    elif 1.5 <= thick < 3.0:
        return {"crit": "СРЕДНЯЯ (Контроль потяжек)", "amp": "60-90A", "el": "2.5-3.0мм", "meth": "Прерывистый шов вразброс.", "cls": ""}
    else:
        return {"crit": "НИЗКАЯ (Стабильный провар)", "amp": "100-140A", "el": "3.0-4.0мм", "meth": "Сплошной шов. Свыше 4мм — разделка кромок.", "cls": "crit-low"}

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
                    price_kg = float(parts[-1].replace(",", "."))
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    prices[name] = {"weight_unit": weight, "price_kg": price_kg, "thick": thick}
                except: continue
    return prices

all_prices = load_prices()

# --- 4. PDF ГЕНЕРАТОР ---
def generate_pdf_bytes(res, weld):
    pdf = FPDF()
    pdf.add_page()
    f_p = "arial.ttf"
    if os.path.exists(f_p):
        pdf.add_font('Arial', '', f_p); pdf.set_font('Arial', '', 14)
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.cell(200, 10, txt=f"ОТЧЕТ IRON WORKS: {res['name']}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font('Arial' if os.path.exists(f_p) else "Helvetica", '', 11)
    for k, v in res['metrics'].items():
        pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="РЕКОМЕНДАЦИИ ПО СВАРКЕ:", ln=True)
    pdf.multi_cell(0, 8, txt=f"Критичность: {weld['crit']}\nТок: {weld['amp']}\nМетод: {weld['meth']}")
    return bytes(pdf.output())

# --- 5. ГЕОМЕТРИЯ ---
def get_box_coords(x0, y0, z0, l, w, h):
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

# --- 6. ИНТЕРФЕЙС ---
with st.sidebar:
    if all_prices:
        sel = st.selectbox("МАТЕРИАЛ:", options=list(all_prices.keys()))
        data = all_prices[sel]
        is_sheet = "Лист" in sel
        st.divider()
        if is_sheet:
            Ls, Ws = st.number_input("Лист L (мм)", 2500.0), st.number_input("Лист W (мм)", 1250.0)
            Ld, Wd = st.number_input("Деталь l (мм)", 600.0), st.number_input("Деталь w (мм)", 400.0)
            Qty = st.number_input("Кол-во (шт)", 10, 1)
        else:
            Lf, Wf, Hf = st.number_input("L рамы (мм)", 2000.0), st.number_input("W рамы (мм)", 1000.0), st.number_input("H рамы (мм)", 1200.0)
            stock_m = st.number_input("Длина трубы (м)", 6.0)
        
        markup = st.slider("Наценка на расходники %", 0, 30, 10)
        calc = st.button("🚀 РАССЧИТАТЬ ВСЁ", use_container_width=True)

# --- 7. РАСЧЕТ И ВЫВОД ---
if calc and all_prices:
    thick = data['thick']
    weld = get_welding_advice(thick)
    report = {"name": sel, "metrics": {}}
    
    if is_sheet:
        on_sheet = max(1, (Ls // Ld) * (Ws // Wd))
        needed = -(-Qty // on_sheet)
        w_buy = data['weight_unit'] * needed
        w_clear = (Ld * Wd * Qty / max(1, (Ls * Ws))) * (data['weight_unit'] * (Qty/on_sheet if on_sheet > 0 else 1)) # Приблизительный чистый вес
        waste = ((w_buy - w_clear) / max(1, w_buy)) * 100
        cost_metal = w_buy * data['price_kg']
        total_price = cost_metal * (1 + markup/100)
        
        report["metrics"] = {"Тип": "Лист", "Толщина": f"{thick}мм", "Купить листов": int(needed), "Вес закупки": f"{w_buy:.1f}кг", "Отход": f"{waste:.1f}%", "ИТОГО": f"{total_price:.0f} грн"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка кг", f"{w_buy:.1f}")
        c2.metric("Чистый вес", f"{w_clear:.1f}")
        c3.metric("Отход %", f"{waste:.1f}", delta=f"{waste:.1f}%", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")
    else:
        m_total = (Lf*4 + Wf*4 + Hf*4) / 1000
        needed_p = -(-m_total // max(0.1, stock_m))
        w_buy = needed_p * stock_m * data['weight_unit']
        w_clear = m_total * data['weight_unit']
        waste = ((w_buy - w_clear) / max(1, w_buy)) * 100
        cost_metal = w_buy * data['price_kg']
        total_price = cost_metal * (1 + markup/100)
        
        report["metrics"] = {"Тип": "Труба", "Палки (6м)": int(needed_p), "Метраж чистый": f"{m_total:.1f}м", "Вес закупки": f"{w_buy:.1f}кг", "Отход": f"{waste:.1f}%", "ИТОГО": f"{total_price:.0f} грн"}
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка кг", f"{w_buy:.1f}")
        c2.metric("Метраж м", f"{m_total:.1f}")
        c3.metric("Отход %", f"{waste:.1f}", delta=f"{waste:.1f}%", delta_color="inverse")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

    # БЛОК ИНЖЕНЕРА (СВАРКА)
    st.subheader("🛠️ Инженерный отдел")
    if waste > 20:
        st.markdown(f'<div class="waste-card">⚠️ <b>Внимание:</b> Высокий процент отхода ({waste:.1f}%). Проверьте размеры заготовок!</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="eng-card {weld['cls']}">
        <b>Критичность сварки:</b> {weld['crit']}<br>
        <b>Рекомендуемый ток:</b> {weld['amp']} | <b>Электрод:</b> {weld['el']}<br>
        <b>Метод:</b> {weld['meth']}
    </div>
    """, unsafe_allow_html=True)

    # 3D
    fig = go.Figure()
    x, y, z = get_box_coords(0,0,0, Ls if is_sheet else Lf, Ws if is_sheet else Wf, thick if is_sheet else Hf)
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='#00c6ff', width=5)))
    fig.update_layout(scene=dict(aspectmode='data'), height=500, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    # КНОПКИ
    col_pdf, col_cad = st.columns(2)
    with col_pdf:
        st.download_button("📥 СКАЧАТЬ ОТЧЕТ (PDF)", data=generate_pdf_bytes(report, weld), file_name="iron_report.pdf")
    with col_cad:
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {Ls if is_sheet else Lf} {Ws if is_sheet else Wf} {thick if is_sheet else Hf}) (princ))", language="lisp")
        