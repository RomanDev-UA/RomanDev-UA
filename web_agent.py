import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. СТИЛИ ИНТЕРФЕЙСА ---
st.set_page_config(page_title="IRON WORKS v15.7", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 20px; }
    .section-head { color: #00c6ff; font-weight: bold; font-size: 18px; margin-top: 15px; border-bottom: 1px solid #333; }
    .download-section { background: #121212; padding: 20px; border-radius: 15px; border: 1px dashed #444; margin-top: 30px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-size: 28px;">🏗️ IRON WORKS | Full Report v15.7</h1></div>', unsafe_allow_html=True)

# --- 2. ФУНКЦИЯ ГЕНЕРАЦИИ PDF ---
def generate_pdf_report(res, w_info):
    pdf = FPDF()
    pdf.add_page()
    
    font_path = "arial.ttf" # Убедись, что файл на GitHub называется именно так
    
    # 1. Пытаемся подключить шрифт
    font_success = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("CustomFont", "", font_path)
            pdf.set_font("CustomFont", "", 16)
            font_success = True
        except:
            pass

    # 2. Если шрифт не загружен - используем латиницу, чтобы не было ошибки
    if not font_success:
        pdf.set_font("Helvetica", "B", 16)
        t_header = "ORDER REPORT"
        t_mat = "Material"
        t_th = "Thick"
        t_wt = "Weight"
        t_total = "TOTAL"
    else:
        t_header = "ОТЧЕТ ПО ЗАКАЗУ - IRON WORKS"
        t_mat = "Материал"
        t_th = "Толщина"
        t_wt = "Общий вес"
        t_total = "ИТОГО К ОПЛАТЕ"

    # Печать заголовка
    pdf.cell(200, 10, txt=t_header, ln=True, align='C')
    pdf.ln(10)
    
    # Печать данных (используем переменные, чтобы избежать кириллицы при ошибке шрифта)
    pdf.set_font(pdf.font_family, "", 12)
    pdf.cell(200, 10, txt=f"{t_mat}: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"{t_th}: {res['thick']} mm", ln=True)
    pdf.cell(200, 10, txt=f"{t_wt}: {res['weight']:.1f} kg", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"{t_total}: {res['total']:.0f} UAH", ln=True)
    
    return bytes(pdf.output()), font_success

# --- В основном блоке кода (где кнопка) ---
if calc_btn:
    # ... твой расчет ...
    
    # Вызываем генерацию
    try:
        pdf_file, is_ok = generate_pdf_report(res_data, w_tech)
        
        if not is_ok:
            st.warning("⚠️ Файл arial.ttf не найден на сервере. Отчет будет на английском.")
            
        st.download_button(
            label="📥 СКАЧАТЬ ОТЧЕТ (PDF)",
            data=pdf_file,
            file_name="Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Ошибка при создании PDF: {e}")


# --- 3. ЗАГРУЗКА БАЗЫ ---
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
                    name, weight, p_unit, p_ton = parts[0].strip(), float(parts[1].replace(',','.')), float(parts[2].replace(',','.')), float(parts[3].replace(',','.'))
                    thick = float(re.findall(r'(\d+\.\d+|\d+)', name)[-1]) if re.findall(r'(\d+\.\d+|\d+)', name) else 2.0
                    catalog[name] = {"weight": weight, "p_unit": p_unit, "p_ton": p_ton, "thick": thick}
                except: continue
    return catalog

def get_weld_tech(thick):
    if thick < 1.8: return {"amp": "40-60А", "electr": "2.0 мм", "meth": "Короткие прихватки"}
    elif thick <= 4.0: return {"amp": "90-135А", "electr": "3.0 мм", "meth": "Сплошной шов"}
    else: return {"amp": "165-210А", "electr": "4.0 мм", "meth": "Разделка + многослойка"}

db = load_db()

# --- 4. ПАНЕЛЬ УПРАВЛЕНИЯ ---
if db:
    with st.sidebar:
        st.markdown('<p class="section-head">📦 МАТЕРИАЛ</p>', unsafe_allow_html=True)
        sel = st.selectbox("Выбор:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Цена:", ["Розница", "Опт"])

        if is_sheet:
            st.markdown('<p class="section-head">📐 ЛИСТ (мм)</p>', unsafe_allow_html=True)
            Ls, Ws = st.number_input("L", 100.0, 6000.0, 2500.0), st.number_input("W", 100.0, 3000.0, 1250.0)
            st.markdown('<p class="section-head">✂️ ДЕТАЛЬ (мм)</p>', unsafe_allow_html=True)
            ld, wd = st.number_input("l", 10.0, 6000.0, 600.0), st.number_input("w", 10.0, 3000.0, 400.0)
            qty = st.number_input("Кол-во", 1, 5000, 12)
        else:
            st.markdown('<p class="section-head">🏗️ КАРКАС (мм)</p>', unsafe_allow_html=True)
            rl, rw, rh = st.number_input("L", 100.0, 10000.0, 2000.0), st.number_input("W", 100.0, 10000.0, 1000.0), st.number_input("H", 100.0, 10000.0, 1200.0)
            stock = st.number_input("Палка (м)", 1.0, 12.0, 6.0)

        markup = st.slider("Наценка (%)", 0, 200, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ", use_container_width=True)

    if calc_btn:
        w_tech = get_weld_tech(item['thick'])
        
        # Логика расчета
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            buy_qty = -(-qty // max(1, nx * ny))
            w_total = buy_qty * item['weight']
            p_base = (buy_qty * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((buy_qty * Ls * Ws - qty * ld * wd) / (buy_qty * Ls * Ws)) * 100
        else:
            m_lin = (rl*4 + rw*4 + rh*4) / 1000
            buy_qty = -(-m_lin // max(0.01, stock))
            w_total = buy_qty * stock * item['weight']
            p_base = (buy_qty * stock * item['p_unit']) if mode == "Розница" else (w_total/1000 * item['p_ton'])
            waste = ((buy_qty * stock - m_lin) / (buy_qty * stock)) * 100

        res_data = {"name": sel, "thick": item['thick'], "buy_qty": buy_qty, "weight": w_total, "waste": waste, "total": p_base * (1 + markup/100)}

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(buy_qty)} ед.")
        c2.metric("Вес", f"{w_total:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{res_data['total']:.0f}")

        # Визуализация
        t1, t2 = st.tabs(["✂️ РАСКРОЙ", "📦 3D"])
        with t1:
            if is_sheet:
                f2 = go.Figure()
                f2.add_shape(type="rect", x0=0, y0=0, x1=Ls, y1=Ws, line=dict(color="White", width=2))
                d_c = 0
                for i in range(nx):
                    for j in range(ny):
                        if d_c < qty:
                            f2.add_shape(type="rect", x0=i*ld, y0=j*wd, x1=(i+1)*ld, y1=(j+1)*wd, fillcolor="#00c6ff", opacity=0.4)
                            d_c += 1
                f2.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(f2, use_container_width=True)
        with t2:
            f3 = go.Figure()
            lx, ly, lz = (Ls, Ws, item['thick']) if is_sheet else (rl, rw, rh)
            if is_sheet:
                f3.add_trace(go.Mesh3d(x=[0,lx,lx,0,0,lx,lx,0], y=[0,0,ly,ly,0,0,ly,ly], z=[0,0,0,0,lz,lz,lz,lz], i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color='#00c6ff', opacity=0.8))
                f3.update_layout(scene=dict(aspectmode='manual', aspectratio=dict(x=1, y=ly/lx, z=0.05), camera=dict(eye=dict(x=1.5, y=1.5, z=0.4))))
            else:
                xc, yc, zc = [0,lx,lx,0,0,0,lx,lx,0,0,None,lx,lx,None,lx,lx,None,0,0],[0,0,ly,ly,0,0,0,ly,ly,0,None,0,0,None,ly,ly,None,ly,ly],[0,0,0,0,0,lz,lz,lz,lz,lz,None,0,lz,None,0,lz,None,0,lz]
                f3.add_trace(go.Scatter3d(x=xc, y=yc, z=zc, mode='lines', line=dict(color='#00c6ff', width=6)))
            f3.update_layout(height=500, paper_bgcolor='#0e1117', margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(f3, use_container_width=True)

        # --- КНОПКА СКАЧИВАНИЯ ---
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        pdf_file = generate_pdf_report(res_data, w_tech)
        st.download_button(
            label="📥 СКАЧАТЬ ПОЛНЫЙ ОТЧЕТ (PDF)",
            data=pdf_file,
            file_name=f"Report_{sel[:10]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
