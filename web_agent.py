import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ ---
st.set_page_config(page_title="IRON WORKS v12.6", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #00c6ff; }
    .eng-card { background-color: #0e2a47; padding: 20px; border-radius: 12px; border-left: 6px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background-color: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div style="background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 25px;"><p style="color: white; font-size: 42px; font-weight: 900; margin: 0;">🏗️ IRON WORKS</p><p style="color: #00c6ff; font-size: 16px; margin: 0;">ROMAN_DEV | STABLE v12.6</p></div>', unsafe_allow_html=True)

# --- 2. ЛОГИКА СВАРКИ ---
def get_welding_advice(thick):
    if thick < 1.5:
        return {"crit": "ВЫСОКАЯ (Риск прожога)", "amp": "30-50A", "el": "1.6-2.0мм", "meth": "Точечно, с паузами.", "cls": "crit-high"}
    elif 1.5 <= thick < 3.0:
        return {"crit": "СРЕДНЯЯ (Контроль потяжек)", "amp": "60-90A", "el": "2.5-3.0мм", "meth": "Прерывистый шов.", "cls": ""}
    else:
        return {"crit": "НИЗКАЯ (Стабильный провар)", "amp": "100-140A", "el": "3.0-4.0мм", "meth": "Сплошной шов.", "cls": "crit-low"}

# --- 3. ПАРСЕР ПРАЙСА ---
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
        pdf.add_font('Arial', '', f_p); pdf.set_font('Arial', '', 12)
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.cell(200, 10, txt=f"REPORT IRON WORKS: {res['name']}", ln=True, align='C')
    pdf.ln(5)
    for k, v in res['metrics'].items():
        pdf.cell(200, 7, txt=f"{k}: {v}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="WELDING TECH CARD:", ln=True)
    pdf.multi_cell(0, 7, txt=f"Crit: {weld['crit']}\nAmp: {weld['amp']}\nMethod: {weld['meth']}")
    return bytes(pdf.output())

# --- 5. ИНТЕРФЕЙС (БЕЗ ОГРАНИЧЕНИЙ MAX) ---
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
            Qty = st.number_input("Кол-во (шт)", value=10, min_value=1)
        else:
            Lf = st.number_input("Рама L (мм)", value=2000.0)
            Wf = st.number_input("Рама W (мм)", value=1000.0)
            Hf = st.number_input("Рама H (мм)", value=1200.0)
            stock_m = st.number_input("Длина трубы (м)", value=6.0)
        
        markup = st.slider("Наценка %", 0, 50, 10)
        calc = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

# --- 6. РАСЧЕТ ---
if calc and all_prices:
    if (is_sheet and (Ls*Ws*Ld*Wd == 0)) or (not is_sheet and (Lf*Wf*Hf == 0)):
        st.error("Размеры не могут быть равны 0!")
    else:
        thick = data['thick']
        weld = get_welding_advice(thick)
        report = {"name": sel, "metrics": {}}
        
        if is_sheet:
            on_sheet = max(1, (Ls // Ld) * (Ws // Wd))
            needed = -(-Qty // on_sheet)
            w_buy = data['weight_unit'] * needed
            w_clear = (Ld * Wd * Qty / max(1, (Ls * Ws))) * w_buy
            waste = ((w_buy - w_clear) / max(1, w_buy)) * 100
            total_price = (w_buy * data['price_kg']) * (1 + markup/100)
            
            report["metrics"] = {"Тип": "Лист", "Кол-во": f"{needed} шт", "Вес": f"{w_buy:.1f}кг", "Отход": f"{waste:.1f}%", "Цена": f"{total_price:.0f}грн"}
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Закупка кг", f"{w_buy:.1f}")
            c2.metric("Чистый вес", f"{w_clear:.1f}")
            c3.metric("Отход", f"{waste:.1f}%", delta_color="inverse")
            c4.metric("ИТОГО ГРН", f"{total_price:.0f}")
        else:
            m_total = (Lf*4 + Wf*4 + Hf*4) / 1000
            needed_p = -(-m_total // max(0.1, stock_m))
            w_buy = needed_p * stock_m * data['weight_unit']
            w_clear = m_total * data['weight_unit']
            waste = ((w_buy - w_clear) / max(1, w_buy)) * 100
            total_price = (w_buy * data['price_kg']) * (1 + markup/100)
            
            report["metrics"] = {"Тип": "Труба", "Палки": int(needed_p), "Вес": f"{w_buy:.1f}кг", "Отход": f"{waste:.1f}%", "Цена": f"{total_price:.0f}грн"}
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Закупка кг", f"{w_buy:.1f}")
            c2.metric("Метраж м", f"{m_total:.1f}")
            c3.metric("Отход", f"{waste:.1f}%", delta_color="inverse")
            c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # ИНЖЕНЕРНЫЙ БЛОК
        st.subheader("🛠️ Инженерный отдел")
        st.markdown(f"""<div class="eng-card"><b>Сварка:</b> {weld['crit']}<br><b>Ток:</b> {weld['amp']} | <b>Метод:</b> {weld['meth']}</div>""", unsafe_allow_html=True)
        
        # 3D
        fig = go.Figure(data=go.Scatter3d(x=[0, Ls if is_sheet else Lf], y=[0, Ws if is_sheet else Wf], z=[0, thick if is_sheet else Hf], mode='markers', marker=dict(size=1, opacity=0)))
        fig.update_layout(scene=dict(aspectmode='data'), height=450, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

        # PDF И КОД
        col_a, col_b = st.columns(2)
        with col_a: st.download_button("📥 СКАЧАТЬ PDF ОТЧЕТ", data=generate_pdf_bytes(report, weld), file_name="iron_report.pdf")
        with col_b: st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {Ls if is_sheet else Lf} {Ws if is_sheet else Wf} {thick if is_sheet else Hf}) (princ))")
        