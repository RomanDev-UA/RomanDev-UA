import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. НАСТРОЙКИ СТИЛЕЙ (Как и было красивым) ---
st.set_page_config(page_title="IRON WORKS v14.9", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .waste-card { background: #2b1b1b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #ff9999; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-weight: 900;">🏗️ IRON WORKS | Final Stable v14.9</h1></div>', unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF (С защитой кодировки) ---
def create_pdf(res, w_info):
    pdf = FPDF()
    pdf.add_page()
    f_file = "arial.ttf"
    
    # Загружаем шрифт если он есть
    if os.path.exists(f_file):
        pdf.add_font("CustomFont", "", f_file)
        pdf.set_font("CustomFont", "", 14)
        t1, t2 = "ТЕХНИЧЕСКАЯ СМЕТА - IRON WORKS", f"Материал: {res['name']}"
    else:
        # Fallback на English если ttf нет
        pdf.set_font("Helvetica", "B", 14)
        t1, t2 = "TECHNICAL ESTIMATE - IRON WORKS", f"Material: {res['name']}"
    
    pdf.cell(200, 10, txt=t1, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica" if not os.path.exists(f_file) else "CustomFont", "", 12)
    
    # Кириллица работает только с ttf
    pdf.multi_cell(0, 10, txt=f"{t2}\n")
    pdf.cell(200, 10, txt=f"Вес закупки: {res['weight']:.1f} кг", ln=True)
    pdf.cell(200, 10, txt=f"Процент отхода: {res['waste']:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"ИТОГО К ОПЛАТЕ: {res['total']:.0f} грн", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=f"Рекомендация по сварке:\nТок: {w_info['amp']}\nЭлектрод: {w_info['electr']}\nТехнология: {w_info['text']}")
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: принудительная конвертация в байты
    return bytes(pdf.output())

# --- 3. ЛОГИКА ИНЖЕНЕРКИ ---
def get_weld_advice(thick):
    if thick < 2.0: return {"amp": "45-65А", "electr": "2.0 мм", "text": "Сварка прихватками, контроль деформаций."}
    elif thick <= 4.0: return {"amp": "90-125А", "electr": "3.0 мм", "text": "Стабильный шов в один проход."}
    else: return {"amp": "160-200А", "electr": "4.0 мм", "text": "Многослойная сварка, разделка кромок."}

# --- 4. DATABASE (Retained) ---
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

# --- 5. INTERFACE (Sidebar) ---
if db:
    with st.sidebar:
        st.header("⚙️ Ввод данных")
        sel = st.selectbox("Материал из базы:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Тип цены:", ["Розница", "Опт (Тонна)"])
        
        if is_sheet:
            Ls, Ws = st.number_input("Лист L (мм)", 1.0, 6000.0, 2500.0), st.number_input("Лист W (мм)", 1.0, 6000.0, 1250.0)
            ld, wd = st.number_input("Деталь l (мм)", 1.0, 6000.0, 600.0), st.number_input("Деталь w (мм)", 1.0, 6000.0, 400.0)
            qty = st.number_input("Кол-во деталей (шт)", 1, 5000, 10)
        else:
            rl, rw, rh = st.number_input("Длина L (мм)", 1.0, 10000.0, 2000.0), st.number_input("Ширина W (мм)", 1.0, 10000.0, 1000.0), st.number_input("Высота H (мм)", 1.0, 10000.0, 1200.0)
            stock = st.number_input("Длина палки (м)", 0.1, 12.0, 6.0)
            
        markup = st.slider("Наценка %", 0, 300, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        w_adv = get_weld_advice(item['thick'])
        
        # Расчет
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_n = -(-qty // max(1, nx * ny))
            w_total = sh_n * item['weight']
            base = (sh_n * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((sh_n * Ls * Ws - qty * ld * wd) / (sh_n * Ls * Ws)) * 100
            lx, ly, lz = Ls, Ws, item['thick']
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            pcs = -(-m_lin // max(0.01, stock))
            w_total = pcs * stock * item['weight']
            base = (pcs * stock * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((pcs * stock - m_lin) / (pcs * stock)) * 100
            lx, ly, lz = rl, rw, rh

        total_price = base * (1 + markup/100)

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_n if is_sheet else pcs)} ед.")
        c2.metric("Вес", f"{w_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_price:.0f}")

        # --- ИНЖЕНЕРНЫЙ БЛОК ---
        st.subheader("🛠️ Расчет сварки")
        st.markdown(f"""
            <div class="eng-card">
                <b>Толщина металла из базы:</b> {item['thick']} мм<br><br>
                <b>Рекомендуемый ток:</b> {w_adv['amp']}<br>
                <b>Электрод:</b> {w_adv['electr']}<br>
                <b>Технология:</b> {w_adv['text']}
            </div>
        """, unsafe_allow_html=True)
        
        if waste > 25:
            st.markdown(f'<div class="waste-card">⚠️ Высокий отход металла ({waste:.1f}%)! Проверьте размеры.</div>', unsafe_allow_html=True)

        # --- КРИТИЧЕСКИЙ ИСПРАВЛЕННЫЙ 3D МОДУЛЬ ---
        st.subheader("📦 3D Визуализация объекта")
        fig = go.Figure()
        
        # Четкие координаты для бокса (трассировка без Mesh)
        xc = [0, lx, lx, 0, 0, 0, lx, lx, 0, 0, None, lx, lx, None, lx, lx, None, 0, 0]
        yc = [0, 0, ly, ly, 0, 0, 0, ly, ly, 0, None, 0, 0, None, ly, ly, None, ly, ly]
        zc = [0, 0, 0, 0, 0, lz, lz, lz, lz, lz, None, 0, lz, None, 0, lz, None, 0, lz]

        # Для листа делаем прозрачную заливку
        if is_sheet:
             fig.add_trace(go.Mesh3d(
                x=[0, lx, lx, 0, 0, lx, lx, 0], y=[0, 0, ly, ly, 0, 0, ly, ly], z=[0, 0, 0, 0, lz, lz, lz, lz],
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color='#00c6ff', opacity=0.6, flatshading=True, name="Лист"
            ))
        
        # Добавляем четкие грани (wireframe) для обоих типов
        fig.add_trace(go.Scatter3d(
            x=xc, y=yc, z=zc,
            mode='lines',
            line=dict(color='#00c6ff', width=6 if not is_sheet else 3)
        ))

        # Настройка камеры (чтобы видеть толщину листа по умолчанию)
        fig.update_layout(
            scene=dict(
                aspectmode='data',
                xaxis_title='L', yaxis_title='W', zaxis_title='Thick' if is_sheet else 'H',
                camera=dict(eye=dict(x=1.8, y=1.8, z=0.5)) # Ракурс немного сбоку
            ),
            height=600, paper_bgcolor='#0e1117'
        )
        st.plotly_chart(fig, use_container_width=True)

        # AutoCAD
        st.subheader("📝 Скрипт AutoCAD")
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")

        # --- 📥 НАКОНЕЦ-ТО ВЕРНУЛАСЬ: КНОПКА PDF ---
        st.divider()
        res_d = {"name": sel, "weight": w_total, "waste": waste, "total": total_price}
        pdf_bytes = create_pdf(res_d, w_adv)
        
        st.download_button(
            label="📥 СКАЧАТЬ СМЕТУ PDF",
            data=pdf_bytes,
            file_name=f"IronWorks_Smeta_{sel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        