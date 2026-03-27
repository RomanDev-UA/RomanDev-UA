import streamlit as st
import os
import plotly.graph_objects as go

# --- 1. КОСМЕТИКА И СТИЛИ ---
st.set_page_config(page_title="IRON WORKS v9.3", layout="wide", page_icon="🏗️")

css_styles = """
    <style>
    .brand-header {
        background: linear-gradient(90deg, #1e2130, #0072ff);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #00c6ff;
        margin-bottom: 25px;
    }
    .brand-title { color: white !important; font-size: 42px; font-weight: 900; margin: 0; letter-spacing: 2px; font-family: sans-serif; }
    .brand-subtitle { color: #00c6ff !important; font-size: 16px; font-weight: 400; margin: 0; font-family: sans-serif; }
    </style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

st.markdown("""
    <div class="brand-header">
        <p class="brand-title">🏗️ IRON WORKS</p>
        <p class="brand-subtitle">ROMAN_DEV PROFESSIONAL ENGINEERING TOOL v9.3</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. ЗАГРУЗКА БАЗЫ ---
@st.cache_data
def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip() or "," not in line: continue
                try:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        name = ",".join(parts[:-2]).strip()
                        prices[name] = {"weight": float(parts[-2].replace(",", ".")), 
                                        "price": float(parts[-1].replace(",", "."))}
                except: continue
    return prices

all_prices = load_prices()

# --- 3. ФУНКЦИЯ LISP ДЛЯ nanoCAD ---
def generate_nanocad_lisp(l, w, h):
    lisp_script = f"""(defun c:IronFrame ()
  (setq p1 '(0 0 0))
  (command "_BOX" p1 "_L" {l} {w} {h})
  (princ "\\nКаркас {l}x{w}x{h} отрисован.")
  (princ)
)"""
    return lisp_script

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        found_name = st.selectbox("ВЫБЕРИТЕ МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name or "Лист" in found_name.capitalize()
        
        st.divider()
        if not is_sheet:
            st.info("🏗️ РЕЖИМ: КАРКАС")
            L_f = st.number_input("Длина L (мм)", value=3000, step=10)
            W_f = st.number_input("Ширина W (мм)", value=1000, step=10)
            H_f = st.number_input("Высота H (мм)", value=500, step=10)
            st.markdown("**📐 Сечение профиля (малярка)**")
            Prof_A = st.number_input("Сторона А (мм)", value=40)
            Prof_B = st.number_input("Сторона Б (мм)", value=20)
        else:
            st.success("📦 РЕЖИМ: ЛИСТ (Раскрой скоро вернем)")
            L_d = st.number_input("Длина детали (мм)", value=800)
            W_d = st.number_input("Ширина детали (мм)", value=400)
            Qty = st.number_input("Кол-во (шт)", value=10)
        
        st.divider()
        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)
    else:
        st.error("Файл prices.txt не найден!")

# --- 5. ВЫВОД РЕЗУЛЬТАТОВ ---
if calc and all_prices:
    st.subheader(f"📊 Результат для: {found_name}")
    
    if not is_sheet:
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        total_len = pure_len * 1.05
        weight_total = total_len * sel['weight']
        cost_total = (weight_total * sel['price']) * 1.10
        paint_area = ((Prof_A + Prof_B) * 2 / 1000) * total_len

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес (+5%)", f"{weight_total:.1f} кг")
        c2.metric("Метраж (м)", f"{total_len:.1f}")
        c3.metric("Малярка м²", f"{paint_area:.2f}")
        c4.metric("Цена (грн)", f"{cost_total:.0f}")

        # --- НОВАЯ ИНТЕРАКТИВНАЯ 3D МОДЕЛЬ (PLOTLY) ---
        st.markdown("### 🏗️ Интерактивная 3D Модель (Крути мышкой!)")
        
        x_lines = []
        y_lines = []
        z_lines = []
        
        # Координаты ребер
        edges = [
            ([0, L_f], [0, 0], [0, 0]), ([0, L_f], [W_f, W_f], [0, 0]),
            ([0, L_f], [0, 0], [H_f, H_f]), ([0, L_f], [W_f, W_f], [H_f, H_f]),
            ([0, 0], [0, W_f], [0, 0]), ([L_f, L_f], [0, W_f], [0, 0]),
            ([0, 0], [0, W_f], [H_f, H_f]), ([L_f, L_f], [0, W_f], [H_f, H_f]),
            ([0, 0], [0, 0], [0, H_f]), ([L_f, L_f], [0, 0], [0, H_f]),
            ([0, 0], [W_f, W_f], [0, H_f]), ([L_f, L_f], [W_f, W_f], [0, H_f])
        ]
        
        for edge in edges:
            x_lines.extend([edge[0][0], edge[0][1], None])
            y_lines.extend([edge[1][0], edge[1][1], None])
            z_lines.extend([edge[2][0], edge[2][1], None])
            
        fig = go.Figure(data=go.Scatter3d(
            x=x_lines, y=y_lines, z=z_lines,
            mode='lines',
            line=dict(color='#00c6ff', width=6)
        ))
        
        fig.update_layout(
            scene=dict(
                aspectmode='data', # ВОТ ЭТО ДАЕТ ИДЕАЛЬНЫЕ ПРОПОРЦИИ
                xaxis_title='Длина L',
                yaxis_title='Ширина W',
                zaxis_title='Высота H'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor='#0e1117',
            font=dict(color='white'),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # --- nanoCAD Код ---
        st.divider()
        st.subheader("🤖 Автоматизация nanoCAD")
        lisp_code = generate_nanocad_lisp(L_f, W_f, H_f)
        st.code(lisp_code, language="lisp")
        st.info("Скопируй код выше, вставь в консоль nanoCAD, нажми Enter, затем введи IronFrame")
        