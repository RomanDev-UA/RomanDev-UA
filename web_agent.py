import streamlit as st
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches

# --- 1. КОСМЕТИКА И СТИЛИ (IRON WORKS BRANDING) ---
st.set_page_config(page_title="IRON WORKS v9.1", layout="wide", page_icon="🏗️")
st.markdown("""
    <style>
    .brand-header {
        background: linear-gradient(90deg, #1e2130, #0072ff);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #00c6ff;
        margin-bottom: 25px;
    }
    .brand-title { color: white; font-size: 42px; font-weight: 900; margin: 0; letter-spacing: 2px; }
    .brand-subtitle { color: #00c6ff; font-size: 16px; font-weight: 400; margin: 0; }
    .stDownloadButton button { width: 100% !important; background-color: #0072ff !important; color: white !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# Логотип на главную
st.markdown("""
    <div class="brand-header">
        <p class="brand-title">🏗️ IRON WORKS</p>
        <p class="brand-subtitle">ROMAN_DEV PROFESSIONAL ENGINEERING TOOL v9.1</p>
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

# --- 3. ФУНКЦИЯ ГЕНЕРАЦИИ LISP ДЛЯ nanoCAD ---
def generate_nanocad_lisp(l, w, h):
    lisp_script = f"""
(defun c:IronFrame ()
  (setq p1 '(0 0 0))
  (setq l {l}) (setq w {w}) (setq h {h})
  (command "_BOX" p1 "_L" l w h)
  (princ "\\nКаркас {l}x{w}x{h} отрисован автоматически.")
  (princ)
)
(princ "\\nВведите IronFrame для отрисовки каркаса.") (princ)
    """
    return lisp_script

# --- 4. БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ ПАРАМЕТРЫ")
    if all_prices:
        found_name = st.selectbox("ВЫБЕРИТЕ МАТЕРИАЛ:", options=list(all_prices.keys()))
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name or "Лист" in found_name.capitalize()
        
        if is_sheet:
            L_d = st.number_input("Длина детали (мм)", value=800)
            W_d = st.number_input("Ширина детали (мм)", value=400)
            Qty = st.number_input("Кол-во (шт)", value=10)
            S_L, S_W = 2500, 1250 # Стандарт
        else:
            L_f = st.number_input("Длина L (мм)", value=2000)
            W_f = st.number_input("Ширина W (мм)", value=1000)
            H_f = st.number_input("Высота H (мм)", value=1200)
            Prof_A = st.number_input("Профиль А (мм)", value=40)
            Prof_B = st.number_input("Профиль Б (мм)", value=20)
        
        calc = st.button("🚀 РАСЧИТАТЬ", use_container_width=True)

# --- 5. ВЫВОД РЕЗУЛЬТАТОВ ---
if calc:
    if not is_sheet:
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        total_len = pure_len * 1.05
        weight_total = total_len * sel['weight']
        cost_total = (weight_total * sel['price']) * 1.10
        paint_area = ((Prof_A + Prof_B) * 2 / 1000) * total_len

        # Метрики
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес", f"{weight_total:.1f} кг")
        c2.metric("Метраж", f"{total_len:.1f} м")
        c3.metric("Малярка", f"{paint_area:.2f} м²")
        c4.metric("Цена", f"{cost_total:.0f} грн")

        # Кнопка для nanoCAD
        st.divider()
        st.subheader("🤖 Автоматизация nanoCAD")
        lisp_code = generate_nanocad_lisp(L_f, W_f, H_f)
        st.code(lisp_code, language="lisp")
        st.info("👆 Скопируй этот код, вставь в командную строку nanoCAD и нажми Enter. Затем введи команду IronFrame")
        
        # 3D Модель (как в v9.0)
        fig = plt.figure(figsize=(8, 4))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#0e1117')
        fig.patch.set_facecolor('#0e1117')
        # ... (отрисовка каркаса) ...
        st.pyplot(fig)
        