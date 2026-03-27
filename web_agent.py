import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF
import io

# --- 1. НАСТРОЙКИ ---
st.set_page_config(page_title="IRON WORKS v13.2", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: #0e2a47; padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF ---
def create_pdf(res, weld_info):
    pdf = FPDF()
    pdf.add_page()
    
    # Попытка загрузить шрифт для кириллицы (должен лежать в папке проекта)
    font_path = "arial.ttf"
    if os.path.exists(font_path):
        pdf.add_font('FreeSans', '', font_path, unicode=True)
        pdf.set_font('FreeSans', '', 14)
    else:
        pdf.set_font('Arial', 'B', 14)

    pdf.cell(200, 10, txt="СМЕТА МЕТАЛЛОКОНСТРУКЦИИ: IRON WORKS", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('Arial' if not os.path.exists(font_path) else 'FreeSans', '', 12)
    pdf.cell(200, 10, txt=f"Материал: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Тип расчета: {res['mode']}", ln=True)
    pdf.cell(200, 10, txt=f"Количество: {res['qty_val']} ед.", ln=True)
    pdf.cell(200, 10, txt=f"Общий вес: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Процент отхода: {res['waste']:.1f}%", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Базовая стоимость металла: {res['base_cost']:.2f} грн", ln=True)
    pdf.cell(200, 10, txt=f"Наценка (расходники/работа): {res['markup']}%", ln=True)
    pdf.set_font('Arial' if not os.path.exists(font_path) else 'FreeSans', 'B', 14)
    pdf.cell(200, 15, txt=f"ИТОГО К ОПЛАТЕ: {res['total']:.0f} грн", ln=True)
    
    pdf.ln(10)
    pdf.set_font('Arial' if not os.path.exists(font_path) else 'FreeSans', 'B', 12)
    pdf.cell(200, 10, txt="ТЕХНИЧЕСКИЕ РЕКОМЕНДАЦИИ:", ln=True)
    pdf.set_font('Arial' if not os.path.exists(font_path) else 'FreeSans', '', 10)
    pdf.multi_cell(0, 7, txt=f"Сварка: {weld_info['crit']}\nТок: {weld_info['amp']}\nМетод: {weld_info['meth']}")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. ПАРСЕР И ЛОГИКА (v13.1) ---
@st.cache_data
def load_db():
    catalog = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line: continue
                try:
                    clean_line = re.sub(r'^\d+:\s*', '', line)
                    parts = clean_line.split(",")
                    name, weight, p_unit, p_ton = parts[0].strip(), float(parts[1]), float(parts[2]), float(parts[3])
                    nums = re.findall(r'(\d+\.\d+|\d+)', name)
                    thick = float(nums[-1]) if nums else 2.0
                    catalog[name] = {"weight": weight, "p_unit": p_unit, "p_ton": p_ton, "thick": thick}
                except: continue
    return catalog

db = load_db()

# --- 4. ИНТЕРФЕЙС ---
st.title("🏗️ IRON WORKS | Сметный отдел")

if db:
    with st.sidebar:
        sel = st.selectbox("Материал:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Цена:", ["Розница", "Опт (Тонна)"])
        
        if is_sheet:
            L, W = st.number_input("Лист L", 2500.0), st.number_input("Лист W", 1250.0)
            dl, dw = st.number_input("Деталь l", 600.0), st.number_input("Деталь w", 400.0)
            qty = st.number_input("Кол-во", 1, 1000, 10)
        else:
            rl, rw, rh = st.number_input("L конструкция", 2000.0), st.number_input("W", 1000.0), st.number_input("H", 1200.0)
            stock = st.number_input("Палка (м)", 6.0)
            
        markup = st.slider("Наценка %", 0, 100, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        # Расчетная логика
        if is_sheet:
            on_sheet = max(1, (L // dl) * (W // dw))
            needed = -(-qty // on_sheet)
            weight_buy = needed * item['weight']
            base = (needed * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((needed * L * W - qty * dl * dw) / (needed * L * W)) * 100
            qty_label = needed
        else:
            m_clear = (rl*4 + rw*4 + rh*4) / 1000
            sticks = -(-m_clear // max(0.1, stock))
            weight_buy = sticks * stock * item['weight']
            base = (sticks * stock * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((sticks * stock - m_clear) / (sticks * stock)) * 100
            qty_label = sticks

        total = base * (1 + markup/100)
        
        # Данные для PDF
        report_data = {
            "name": sel, "mode": mode, "qty_val": qty_label, "weight": weight_buy, 
            "waste": waste, "base_cost": base, "markup": markup, "total": total
        }
        
        # Сварка
        w_advice = {"crit": "Высокая" if item['thick'] < 2 else "Норма", "amp": "50-130A", "meth": "Согласно техпроцессу"}

        # Вывод
        c1, c2, c3 = st.columns(3)
        c1.metric("ИТОГО ГРН", f"{total:.0f}")
        c2.metric("ВЕС", f"{weight_buy:.1f} кг")
        c3.metric("МАТЕРИАЛ", f"{qty_label} ед.")

        st.divider()
        
        # КНОПКА СКАЧИВАНИЯ
        pdf_bytes = create_pdf(report_data, w_advice)
        st.download_button(
            label="📥 СКАЧАТЬ СМЕТУ (PDF)",
            data=pdf_bytes,
            file_name=f"Smeta_{sel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.success("Смета готова! Нажмите кнопку выше, чтобы сохранить файл.")
        