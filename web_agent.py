import streamlit as st
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches

# --- 1. НАСТРОЙКИ СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="RomanDev IronWorks Pro", layout="wide", page_icon="⚙️")
st.markdown("""
    <style>
    .main-title { font-size: 40px; font-weight: 800; background: -webkit-linear-gradient(#00c6ff, #0072ff);
                  -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding-bottom:10px;}
    .report-box { background-color: #1e2130; padding: 20px; border-radius: 15px; border: 1px solid #3e445b; font-family: monospace;}
    stActionButton {border-radius: 20px !important;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">⚔️ ROMAN_DEV | IRON WORKS v9.0 Pro</p>', unsafe_allow_html=True)

# --- 2. ЗАГРУЗКА БАЗЫ ЦЕН (Файл prices.txt) ---
@st.cache_data # Кэшируем, чтобы не читать файл каждый раз
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

# --- 3. АЛГОРИТМ ПРОСТОГО РАСКРОЯ (NESTING) ---
def perform_nesting(part_l, part_w, qty, sheet_l, sheet_w, margin=5):
    """Примитивный алгоритм раскроя прямоугольников на листах"""
    sheets = []
    current_sheet_parts = []
    
    # Сортируем детали по убыванию длинной стороны (жадный алгоритм)
    p_l = max(part_l, part_w) + margin
    p_w = min(part_l, part_w) + margin
    s_l = max(sheet_l, sheet_w)
    s_w = min(sheet_l, sheet_w)
    
    if p_l > s_l or p_w > s_w:
        return None, "Деталь больше заготовки!"

    parts_to_place = qty
    
    while parts_to_place > 0:
        current_sheet_parts = []
        current_x = 0
        current_y = 0
        row_h = 0
        
        placed_on_this_sheet = 0
        
        # Заполняем рядами
        while current_y + p_w <= s_w:
            current_x = 0
            row_h = 0
            while current_x + p_l <= s_l and parts_to_place > 0:
                # Кладем деталь (координаты X, Y, W, H)
                current_sheet_parts.append((current_x, current_y, p_l-margin, p_w-margin))
                current_x += p_l
                row_h = p_w
                parts_to_place -= 1
                placed_on_this_sheet += 1
            if placed_on_this_sheet == 0: break # Не влезла ни одна деталь в ряд
            current_y += row_h
            if parts_to_place == 0: break
            
        if placed_on_this_sheet == 0 and parts_to_place > 0:
            return None, "Критическая ошибка раскроя (не влазит)"

        sheets.append(current_sheet_parts)
        if len(sheets) > 50: break # Защита от бесконечного цикла
        
    return sheets, None

# --- 4. БОКОВАЯ ПАНЕЛЬ (ВВОД ДАННЫХ) ---
with st.sidebar:
    st.header("🛠️ НАСТРОЙКИ ЗАКАЗА")
    if all_prices:
        mat_options = list(all_prices.keys())
        found_name = st.selectbox("1. МАТЕРИАЛ (из prices.txt):", options=mat_options)
        sel = all_prices[found_name]
        is_sheet = "Лист" in found_name or "Лист" in found_name.capitalize()
        
        st.divider()
        if is_sheet:
            st.success("📦 РЕЖИМ: РАСКРОЙ ЛИСТА")
            col1, col2 = st.columns(2)
            L_d = col1.number_input("Длина дет. (мм)", min_value=1, value=800)
            W_d = col2.number_input("Ширина дет. (мм)", min_value=1, value=400)
            Qty = st.number_input("Количество (шт)", min_value=1, value=12)
            
            st.markdown("**📐 Размер заготовки (Листа)**")
            sheet_type = st.selectbox("Стандарт:", ["1250x2500", "1500x3000", "1000x2000", "Свой размер"])
            if sheet_type == "Свой размер":
                S_L = st.number_input("Длина заготовки (мм)", value=2500)
                S_W = st.number_input("Ширина заготовки (мм)", value=1250)
            else:
                dims = sheet_type.split("x")
                S_L = int(dims[1]); S_W = int(dims[0])
            Kerf = st.number_input("Запас на рез (мм)", value=5)

        else:
            st.info("🏗️ РЕЖИМ: КАРКАС / ПРОКАТ")
            L_f = st.number_input("Длина L (мм)", min_value=1, value=2500, step=10)
            W_f = st.number_input("Ширина W (мм)", min_value=1, value=1200, step=10)
            H_f = st.number_input("Высота H (мм)", min_value=1, value=1000, step=10)
            
            st.markdown("**📐 Сечение профиля (малярка)**")
            Prof_A = st.number_input("Сторона А (мм)", min_value=1, value=40)
            Prof_B = st.number_input("Сторона Б (мм)", min_value=1, value=20)
            
        st.divider()
        calc = st.button("🚀 ВЫПОЛНИТЬ ИНЖЕНЕРНЫЙ РАСЧЕТ", use_container_width=True)
    else:
        st.error("Файл prices.txt не найден! Проверь GitHub.")

# --- 5. ОСНОВНОЙ ЭКРАН (ВЫВОД РЕЗУЛЬТАТОВ) ---
if calc and all_prices:
    st.subheader(f"📊 Результат для: {found_name}")
    
    if is_sheet:
        # --- ЛОГИКА РАСКРОЯ ЛИСТА ---
        with st.spinner('Считаем оптимальный раскрой...'):
            nesting_results, error = perform_nesting(L_d, W_d, Qty, S_L, S_W, Kerf)
        
        if error:
            st.error(f"❌ Ошибка раскроя: {error}")
        else:
            num_sheets = len(nesting_results)
            area_one_det = (L_d * W_d) / 1_000_000
            area_all_det = area_one_det * Qty
            area_one_sheet = (S_L * S_W) / 1_000_000
            area_total_sheets = area_one_sheet * num_sheets
            
            real_waste_prc = ((area_total_sheets - area_all_det) / area_total_sheets) * 100
            weight_total = area_total_sheets * sel['weight']
            cost_total = (weight_total * sel['price']) * 1.10 # +10% расходники

            # Метрики
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Купить ЛИСТОВ", f"{num_sheets} шт", f"{S_W}x{S_L}")
            c2.metric("Общий вес", f"{weight_total:.1f} кг")
            c3.metric("Чистый Вес Дет.", f"{area_all_det * sel['weight']:.1f} кг")
            c4.metric("Итого ЦЕНА", f"{cost_total:.0f} грн")
            st.caption(f"ℹ️ Реальный остаток (обрезь): {real_waste_prc:.1f}% от закупленного металла.")

            # --- ЧЕРТЕЖ РАСКРОЯ (2D) ---
            st.markdown(f"### ✂️ Схема раскроя (Листов: {num_sheets})")
            
            # Показываем максимум 3 листа, чтобы не перегружать
            sheets_to_show = nesting_results[:3]
            fig_w = 12
            fig_h = (S_W / S_L) * fig_w * len(sheets_to_show)
            if fig_h < 5: fig_h = 5
            
            fig, axs = plt.subplots(len(sheets_to_show), 1, figsize=(fig_w, fig_h), squeeze=False)
            fig.patch.set_facecolor('#0e1117')

            for i, sheet_parts in enumerate(sheets_to_show):
                ax = axs[i, 0]
                ax.set_facecolor('#1e2130')
                ax.set_title(f"Лист №{i+1} ({S_W}x{S_L} мм)", color='white', fontsize=14)
                
                # Рисуем контур листа
                rect_sheet = patches.Rectangle((0, 0), S_L, S_W, linewidth=2, edgecolor='#0072ff', facecolor='none', linestyle='--')
                ax.add_patch(rect_sheet)
                
                # Рисуем детали
                for x, y, w, h in sheet_parts:
                    rect_det = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='#00c6ff', facecolor='#00c6ff', alpha=0.3)
                    ax.add_patch(rect_det)
                    # Если деталь не слишком мелкая, подпишем размер
                    if w > 200 and h > 100 and i==0:
                         ax.text(x + w/2, y + h/2, f"{int(w)}x{int(h)}", color='white', ha='center', va='center', fontsize=8)
                
                ax.set_xlim(-50, S_L + 50)
                ax.set_ylim(-50, S_W + 50)
                ax.set_aspect('equal')
                ax.axis('off') # Убираем оси

            plt.tight_layout()
            st.pyplot(fig)
            
            if num_sheets > 3:
                st.warning(f"Остальные {num_sheets-3} листов раскроены аналогично.")

            report_text = f"ОТЧЕТ: РАСКРОЙ ЛИСТОВ v9.0\n------------------\nМатериал: {found_name}\nДеталь: {L_d}x{W_d} мм ({Qty} шт)\nЗаготовка: {S_W}x{S_L} мм\nНУЖНО КУПИТЬ: {num_sheets} целых листов\nОбщий вес: {weight_total:.1f} кг\nИтого цена: {cost_total:.0f} грн"

    else:
        # --- ЛОГИКА КАРКАСА (УЛУЧШЕННОЕ 3D) ---
        pure_len = ((L_f*4)+(W_f*4)+(H_f*4))/1000
        total_len = pure_len * 1.05 # +5% запас
        weight_total = total_len * sel['weight']
        cost_total = (weight_total * sel['price']) * 1.10 # +10% расходники
        paint_area = ((Prof_A + Prof_B) * 2 / 1000) * total_len

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Вес (+5%)", f"{weight_total:.1f} кг")
        c2.metric("Метраж (м)", f"{total_len:.1f}")
        c3.metric("Малярка м²", f"{paint_area:.2f}")
        c4.metric("Цена (грн)", f"{cost_total:.0f}")

        # Улучшенная 3D Модель
        st.markdown("### 🏗️ 3D Визуализация (утолщенная)")
        fig = plt.figure(figsize=(10, 6))
        fig.patch.set_facecolor('#0e1117')
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#0e1117')
        
        # Определяем толщину линий в 3D в зависимости от сечения профиля
        line_w = 2 + (max(Prof_A, Prof_B) / 10)
        if line_w > 10: line_w = 10
        
        edges = [
            ([0, L_f], [0, 0], [0, 0]), ([0, L_f], [W_f, W_f], [0, 0]),
            ([0, L_f], [0, 0], [H_f, H_f]), ([0, L_f], [W_f, W_f], [H_f, H_f]),
            ([0, 0], [0, W_f], [0, 0]), ([L_f, L_f], [0, W_f], [0, 0]),
            ([0, 0], [0, W_f], [H_f, H_f]), ([L_f, L_f], [0, W_f], [H_f, H_f]),
            ([0, 0], [0, 0], [0, H_f]), ([L_f, L_f], [0, 0], [0, H_f]),
            ([0, 0], [W_f, W_f], [0, H_f]), ([L_f, L_f], [W_f, W_f], [0, H_f])
        ]
        
        for x, y, z in edges:
            ax.plot(x, y, z, color='#00c6ff', linewidth=line_w, marker='o', markersize=3, markeredgecolor='white')

        # Настройка осей
        ax.set_xlabel('Длина L, мм', color='gray')
        ax.set_ylabel('Ширина W, мм', color='gray')
        ax.set_zlabel('Высота H, мм', color='gray')
        ax.grid(True, color='#3e445b', linestyle='--')
        
        # Фикс одинакового масштаба осей
        max_dim = max(L_f, W_f, H_f)
        ax.set_xlim(0, max_dim); ax.set_ylim(0, max_dim); ax.set_zlim(0, max_dim)
        
        st.pyplot(fig)
        
        report_text = f"ОТЧЕТ: КАРКАС v9.0\nМатериал: {found_name}\nРазмеры: {L_f}x{W_f}x{H_f} мм\nВес: {weight_total:.1f} кг\nПокраска: {paint_area:.2f} м2\nЦена: {cost_total:.0f} грн"

    # --- 6. КНОПКА СКАЧИВАНИЯ ---
    st.divider()
    st.markdown("### 💾 Сохранить результат")
    st.download_button("📥 СКАЧАТЬ ТЕКСТОВЫЙ ОТЧЕТ (.TXT)", report_text, file_name="IronWorks_Report.txt", use_container_width=True)

