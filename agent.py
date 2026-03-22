import os
from datetime import datetime
# Импортируем твой уникальный алгоритм
from modules.optimizer import optimize_cutting

def load_prices():
    filename = "prices.txt"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            # Начальный прайс (можно менять в самом файле prices.txt)
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
    """ Базовая логика каркаса со стойками и перемычками """
    levels = int(H / step)
    return [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Перемычка L", "qty": levels * 2, "size": L},
        {"item": "Перемычка W", "qty": levels * 2, "size": W}
    ]

# --- ГЛАВНЫЙ ЭКРАН ---
print("--- RomanDev Engineering Suite v3.7 (PRO Edition) ---")

while True:
    metal_base = load_prices()
    print("\n" + "="*60)
    user_input = input("Введите L, W, H (через запятую в мм) или 'выход': ")
    if user_input.lower() == 'выход': break
    
    try:
        L, W, H = map(float, user_input.split(','))
        
        print("\nВЫБЕРИТЕ ТИП МЕТАЛЛА:")
        for k, v in metal_base.items(): print(f"{k}. {v['name']}")
        choice = input("Номер позиции: ")
        sel = metal_base.get(choice, metal_base["2"])
        
        # 1. Генерируем список всех деталей каркаса
        details = calculate_frame(L, W, H)
        all_pieces = []
        for d in details:
            for _ in range(int(d['qty'])):
                all_pieces.append(d['size'])
        
        # 2. ЗАПУСКАЕМ ОПТИМИЗАТОР (Хлысты по 6000 мм, рез 3 мм)
        bins = optimize_cutting(all_pieces, 6000, kerf=3)
        
        # --- ВЫВОД ИНСТРУКЦИИ ДЛЯ РЕЗКИ ---
        print(f"\n📋 КАРТА РАСКРОЯ ({sel['name']}):")
        print(f"Всего труб к закупке: {len(bins)} шт. по 6 метров")
        print("-" * 40)
        
        for i, b in enumerate(bins, 1):
            cuts_str = " + ".join([f"{int(c)}мм" for c in b["cuts"]])
            print(f"Труба №{i}: [{cuts_str}] | Остаток: {int(b['rem'])}мм")
        print("-" * 40)

        # --- ЭКОНОМИКА И ВЕС ---
        total_m_bought = len(bins) * 6
        mat_cost = total_m_bought * sel['price']
        total_weight = total_m_bought * sel['weight']
        
        print(f"💰 СУММА К ОПЛАТЕ: {mat_cost:.0f} грн")
        print(f"⚖️ ОБЩИЙ ВЕС: {total_weight:.1f} кг")

        # --- СОХРАНЕНИЕ В СМЕТУ ---
        with open("SMETA.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {L}x{W}x{H} ({sel['name']})\n")
            f.write(f"Закупка: {len(bins)} хлыстов. Итого: {mat_cost:.0f} грн\n")
            for i, b in enumerate(bins, 1):
                f.write(f"  Хлыст {i}: {b['cuts']} (ост. {int(b['rem'])}мм)\n")
            f.write("-" * 40 + "\n")

        print(f"\n✅ Расчет завершен. Данные в SMETA.txt")

    except Exception as e:
        print(f"❌ Ошибка ввода: {e}. Используйте формат: 2000, 1000, 1500")
        