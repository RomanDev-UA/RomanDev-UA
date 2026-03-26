import os
from datetime import datetime
import re

# --- ИМПОРТЫ МОДУЛЕЙ ---
try:
    from modules.optimizer import optimize_cutting
    from modules.renderer import generate_3d_model
    from modules.pdf_report import create_pdf_report
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}. Проверь папку modules!")

def load_prices():
    prices = {}
    if os.path.exists("prices.txt"):
        with open("prices.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    try:
                        k, data = line.strip().split(":")
                        name, w, p = data.split(",")
                        prices[k] = {"name": name, "weight": float(w), "price": float(p)}
                    except: continue
    return prices

def calculate_frame(L, W, H, step=500):
    levels = max(1, int(H / step))
    return [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Перемычка L", "qty": levels * 2, "size": L},
        {"item": "Перемычка W", "qty": levels * 2, "size": W}
    ]

print("--- RomanDev Engineering Suite v5.0 (Full Integration) ---")

while True:
    metal_base = load_prices()
    print("\n" + "="*60)
    user_input = input("Введите L, W, H (мм) через запятую или 'выход': ")
    if user_input.lower() in ['выход', 'exit']: break
    
    try:
        L, W, H = map(float, user_input.split(','))
        search = input("🔍 Что ищем? (номер или название): ").lower()
        filtered = {k: v for k, v in metal_base.items() if search in v['name'].lower() or search == k}
        
        if not filtered: filtered = metal_base
        for k, v in filtered.items(): print(f"{k}. {v['name']}")
        
        choice = input("Номер позиции: ")
        sel = filtered.get(choice, list(filtered.values())[0])

        # 1. Расчет деталей
        details = calculate_frame(L, W, H)
        all_pieces = [d['size'] for d in details for _ in range(int(d['qty']))]
        
        # 2. Оптимизация (хлысты 6м, рез 3мм)
        bins = optimize_cutting(all_pieces, 6000, kerf=3)
        
        # 3. Экономика и Физика
        total_cost = len(bins) * 6 * sel['price']
        total_weight = len(bins) * 6 * sel['weight']
        net_weight = (sum(all_pieces) / 1000) * sel['weight']
        waste_percent = ((total_weight - net_weight) / total_weight) * 100
        
        # Извлекаем толщину стенки (последнее число в названии)
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", sel['name'])
        wall = float(nums[-1]) if nums else 2.0

        if wall <= 1.5:
            risk, advice = "КРИТИЧЕСКИЙ", "Варить только прихватками! Металл ведет."
        elif wall <= 3.0:
            risk, advice = "УМЕРЕННЫЙ", "Соблюдать очередность швов. Стандартный ток."
        else:
            risk, advice = "НИЗКИЙ", "Можно варить сплошным швом. Высокая жесткость."

        # --- ГЕНЕРАЦИЯ ---
        generate_3d_model(L, W, H, details, t=40)
        
        # ПЕРЕДАЧА В PDF (Обрати внимание на новые аргументы!)
        create_pdf_report(L, W, H, sel['name'], total_cost, total_weight, bins, advice, waste_percent)

        print(f"\n✅ ГОТОВО! Вес: {total_weight:.1f}кг | Отходы: {waste_percent:.1f}%")
        print(f"📢 Совет: {advice}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        