import os
from datetime import datetime

# --- ИМПОРТЫ МОДУЛЕЙ (В НАЧАЛЕ) ---
from modules.optimizer import optimize_cutting
from modules.renderer import generate_3d_model
from modules.pdf_report import create_pdf_report  # Наш новый "печатный цех"

def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    k, data = line.strip().split(":")
                    name, w, p = data.split(",")
                    prices[k] = {"name": name, "weight": float(w), "price": float(p)}
    return prices

def calculate_frame(L, W, H, step=500):
    levels = int(H / step)
    if levels < 1: levels = 1
    return [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Перемычка L", "qty": levels * 2, "size": L},
        {"item": "Перемычка W", "qty": levels * 2, "size": W}
    ]

print("--- RomanDev Engineering Suite v5.0 (Full PDF & 3D) ---")

while True:
    metal_base = load_prices()
    print("\n" + "="*60)
    user_input = input("Введите L, W, H (мм) через запятую или 'выход': ")
    if user_input.lower() in ['выход', 'exit', 'quit']: break
    
    try:
        # Парсим ввод
        L, W, H = map(float, user_input.split(','))
        
        # Поиск металла
        search = input("🔍 Какой профиль ищем? (напр. 40 или 'все'): ").lower()
        filtered = {k: v for k, v in metal_base.items() if search in v['name'].lower() or search == 'все'}
        if not filtered: filtered = metal_base
        
        for k, v in filtered.items(): print(f"{k}. {v['name']}")
        choice = input("Номер позиции из списка: ")
        sel = filtered.get(choice, list(filtered.values())[0])

        # 1. Расчет деталей
        details = calculate_frame(L, W, H)
        all_pieces = [d['size'] for d in details for _ in range(int(d['qty']))]
        
        # 2. Оптимизация нарезки (хлысты по 6000мм, рез 3мм)
        bins = optimize_cutting(all_pieces, 6000, kerf=3)
        
        # 3. Экономика
        total_cost = len(bins) * 6 * sel['price']
        total_weight = len(bins) * 6 * sel['weight']

        # 4. Определяем толщину для 3D (ищем цифру в названии)
        t_val = 40
        for word in sel['name'].replace('х',' ').split():
            if word.replace('.','',1).isdigit():
                t_val = float(word)
                break

        # --- ВОТ ТУТ В КОНЦЕ МЫ ВСТАВЛЯЕМ ГЕНЕРАЦИЮ ФАЙЛОВ ---
        
        # Генерируем 3D-модель (теперь со всеми перемычками)
        generate_3d_model(L, W, H, details, t_val)
        
        # Генерируем PDF-отчет для печати
        create_pdf_report(L, W, H, sel['name'], total_cost, total_weight, bins)

        print(f"\n✅ РАСЧЕТ ЗАВЕРШЕН!")
        print(f"💰 Цена: {total_cost:.0f} грн | Вес: {total_weight:.1f} кг")
        print(f"📦 Созданы файлы: 'frame_model.obj' и 'Order_Report.pdf'")

    except Exception as e:
        print(f"❌ Ошибка в расчетах: {e}")

print("\nПрограмма завершена. Хорошего дня, Роман!")
