import os
from datetime import datetime
# Подключаем твой уникальный модуль
from modules.optimizer import optimize_cutting

def load_prices():
    filename = "prices.txt"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("1:Труба 20x20x2,1.08,65\n2:Труба 40x40x2,2.33,130\n3:Труба 60x40x2,2.96,170")
    
    prices = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                k, data = line.strip().split(":")
                name, w, p = data.split(",")
                prices[k] = {"name": name, "weight": float(w), "price": float(p)}
    return prices

def calculate_frame(L, W, H, step=500):
    levels = int(H / step)
    return [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Перемычка L", "qty": levels * 2, "size": L},
        {"item": "Перемычка W", "qty": levels * 2, "size": W}
    ]

print("--- RomanDev Engineering Suite v3.5 (Optimizer Active) ---")

while True:
    metal_base = load_prices()
    print("\n" + "="*50)
    user_input = input("Введите L, W, H (мм) через запятую или 'выход': ")
    if user_input.lower() == 'выход': break
    
    try:
        L, W, H = map(float, user_input.split(','))
        
        print("\nВЫБЕРИТЕ МЕТАЛЛ:")
        for k, v in metal_base.items(): print(f"{k}. {v['name']}")
        choice = input("Номер: ")
        sel = metal_base.get(choice, metal_base["2"])
        
        details = calculate_frame(L, W, H)
        
        # 1. Собираем список всех отрезков для резки
        all_pieces = []
        for d in details:
            for _ in range(int(d['qty'])):
                all_pieces.append(d['size'])
        
        # 2. ЗАПУСКАЕМ ТВОЙ ОПТИМИЗАТОР (стандарт хлыста 6000 мм)
        # Он берет функцию из твоего файла modules/optimizer.py
        num_stocks, leftovers = optimize_cutting(all_pieces, 6000)
        
        # 3. Считаем экономику по целым трубам
        total_m_bought = num_stocks * 6 
        mat_cost = total_m_bought * sel['price']
        total_weight = total_m_bought * sel['weight']
        
        # ВЫВОД РЕЗУЛЬТАТА
        print(f"\n🚀 ТВОЕ НОУ-ХАУ В ДЕЙСТВИИ:")
        print(f"📦 Нужно купить целых труб (6м): {num_stocks} шт.")
        print(f"💰 Сумма закупки на базе: {mat_cost:.0f} грн")
        print(f"⚖️ Вес металла: {total_weight:.1f} кг")
        
        print(f"\n✂️ КАРТА ОСТАТКОВ (мм от каждой трубы):")
        print(f"{[round(x, 0) for x in leftovers]}")

        # Сохраняем в Смету
        with open("SMETA.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%d.%m %H:%M')}] Расчет для {sel['name']}\n")
            f.write(f"Размеры изделия: {L}x{W}x{H} мм\n")
            f.write(f"Закупка: {num_stocks} хлыстов по 6м. Остатки: {leftovers}\n")
            f.write("-" * 30 + "\n")

    except Exception as e:
        print(f"❌ Ошибка в расчетах: {e}")
        
        
