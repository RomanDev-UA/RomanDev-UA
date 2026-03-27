import streamlit as st
import os
import plotly.graph_objects as go
import re
from fpdf import FPDF

# --- 1. ГРАФИЧЕСКАЯ ОБОЛОЧКА ---
st.set_page_config(page_title="IRON WORKS v16.0", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .stMetric { background: #1e2130; padding: 15px; border-radius: 12px; border: 1px solid #00c6ff; }
    .eng-card { background: linear-gradient(135deg, #0e2a47, #163a5f); padding: 20px; border-radius: 15px; border-left: 8px solid #00c6ff; color: #e0f4ff; margin-bottom: 20px; }
    .main-header { background: linear-gradient(90deg, #1e2130, #0072ff); padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #00c6ff; margin-bottom: 20px; }
    .section-head { color: #00c6ff; font-weight: bold; font-size: 18px; margin-top: 15px; border-bottom: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 style="color: white; margin: 0; font-size: 28px;">🏗️ IRON WORKS | Professional v16.0</h1></div>', unsafe_allow_html=True)

# --- 2. ГЕНЕРАТОР PDF (С ЗАЩИТОЙ ОТ ОШИБОК) ---
def generate_pdf_report(res, w_info):
    pdf = FPDF()
    pdf.add_page()
    font_path = "arial.ttf"
    
    # Проверка шрифта
    font_ok = False
    if os.path.exists(font_path):
        try:
            pdf.add_font("CustomFont", "", font_path)
            pdf.set_font("CustomFont", "", 16)
            font_ok = True
        except: pass

    if not font_ok:
        pdf.set_font("Helvetica", "B", 16)
        txts = {"h": "ORDER REPORT", "m": "Material", "w": "Weight", "t": "TOTAL"}
    else:
        txts = {"h": "ОТЧЕТ ПО ЗАКАЗУ - IRON WORKS", "m": "Материал", "w": "Общий вес", "t": "ИТОГО К ОПЛАТЕ"}

    pdf.cell(200, 10, txt=txts["h"], ln=True, align='C')
    pdf.ln(10)
    pdf.set_font(pdf.font_family, "", 12)
    pdf.cell(200, 10, txt=f"{txts['m']}: {res['name']}", ln=True)
    pdf.cell(200, 10, txt=f"{txts['w']}: {res['weight']:.1f} kg", ln=True)
    pdf.cell(200, 10, txt=f"{txts['t']}: {res['total']:.0f} UAH", ln=True)
    
    return bytes(pdf.output()), font_ok

# --- 3. БАЗА ДАННЫХ ---
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
    if thick < 1.8: return {"amp": "40-60А", "electr": "2.0 мм", "meth": "Прихватки"}
    elif thick <= 4.0: return {"amp": "90-135А", "electr": "3.0 мм", "meth": "Сплошной шов"}
    else: return {"amp": "165-210А", "electr": "4.0 мм", "meth": "Разделка кромок"}

# --- 4. ОСНОВНОЙ ЦИКЛ ПРИЛОЖЕНИЯ ---
db = load_db()
calc_btn = False # Инициализация для избежания NameError

if db:
    with st.sidebar:
        st.markdown('<p class="section-head">📦 МАТЕРИАЛ</p>', unsafe_allow_html=True)
        sel = st.selectbox("Выбор из базы:", list(db.keys()))
        item = db[sel]
        is_sheet = "Лист" in sel
        mode = st.radio("Тип цены:", ["Розница", "Опт (Тонна)"])

        if is_sheet:
            st.markdown('<p class="section-head">📐 ЛИСТ (мм)</p>', unsafe_allow_html=True)
            Ls, Ws = st.number_input("Длина листа L", 100.0, 6000.0, 2500.0), st.number_input("Ширина листа W", 100.0, 3000.0, 1250.0)
            st.markdown('<p class="section-head">✂️ ДЕТАЛЬ (мм)</p>', unsafe_allow_html=True)
            ld, wd = st.number_input("Длина детали l", 10.0, 6000.0, 600.0), st.number_input("Ширина детали w", 10.0, 3000.0, 400.0)
            qty = st.number_input("Кол-во штук", 1, 5000, 10)
        else:
            st.markdown('<p class="section-head">🏗️ КАРКАС (мм)</p>', unsafe_allow_html=True)
            rl, rw, rh = st.number_input("L", 100.0, 10000.0, 2000.0), st.number_input("W", 100.0, 10000.0, 1000.0), st.number_input("H", 100.0, 10000.0, 1200.0)
            stock = st.number_input("Длина проката (м)", 1.0, 12.0, 6.0)

        markup = st.slider("Наценка (%)", 0, 200, 15)
        calc_btn = st.button("🚀 РАССЧИТАТЬ СМЕТУ", use_container_width=True)

    # --- ЛОГИКА ВЫВОДА (ТОЛЬКО ПОСЛЕ НАЖАТИЯ) ---
    if calc_btn:
        w_tech = get_weld_tech(item['thick'])
        
        if is_sheet:
            nx, ny = int(Ls // ld), int(Ws // wd)
            sh_needed = -(-qty // max(1, nx * ny))
            weight_buy = sh_needed * item['weight']
            price_base = (sh_needed * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((sh_needed * Ls * Ws - qty * ld * wd) / (sh_needed * Ls * Ws)) * 100
        else:
            m_total = (rl*4 + rw*4 + rh*4) / 1000
            sh_needed = -(-m_total // max(0.01, stock)) # Тут это кол-во палок
            weight_buy = sh_needed * stock * item['weight']
            price_base = (sh_needed * stock * item['p_unit']) if mode == "Розница" else (weight_buy/1000 * item['p_ton'])
            waste = ((sh_needed * stock - m_total) / (sh_needed * stock)) * 100

        total_final = price_base * (1 + markup/100)
        res_summary = {"name": sel, "weight": weight_buy, "total": total_final}

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Закупка", f"{int(sh_needed)} ед.")
        c2.metric("Вес", f"{weight_buy:.1f} кг")
        c3.metric("Отход", f"{waste:.1f}%")
        c4.metric("ИТОГО ГРН", f"{total_final:.0f}")

        # Визуализация
        tab1, tab2 = st.tabs(["✂️ РАСКРОЙ", "📦 3D МОДЕЛЬ"])
        with tab1:
            if is_sheet:
                f2 = go.Figure()
                f2.add_shape(type="rect", x0=0, y0=0, x1=Ls, y1=Ws, line=dict(color="White", width=2))
                d_c = 0
                for i in range(nx):
                    for j in range(ny):
                        if d_c < qty:
                            f2.add_shape(type="rect", x0=i*ld, y0=j*wd, x1=(i+1)*ld, y1=(j+1)*wd, fillcolor="#00c6ff", opacity=0.4)
                            d_c += 1
                f2.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0))
                st.plotly_chart(f2, use_container_width=True)
            else:
                st.info("Раскрой доступен для листового металла.")

        with tab2:
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

        # ФИНАЛЬНАЯ КНОПКА СКАЧИВАНИЯ
        st.divider()
        try:
            pdf_data, is_font = generate_pdf_report(res_summary, w_tech)
            if not is_font: st.warning("Шрифт arial.ttf не найден. Отчет на английском.")
            st.download_button("📥 СКАЧАТЬ ОТЧЕТ (PDF)", pdf_data, "IronWorks_Report.pdf", "application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка PDF: {e}")
        
        st.code(f"(defun c:IronCAD () (command \"_BOX\" '(0 0 0) \"_L\" {lx} {ly} {lz}) (princ))")
else:
    st.error("Ошибка: Проверьте наличие файла prices.txt")
    