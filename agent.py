import os
from datetime import datetime

# --- 1. ЗАГРУЗКА ЦЕН ---
def load_prices():
    filename = "prices.txt"
    if not os.path.exists(filename):
        # Базовый набор (Название, Вес, Цена)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("1:Труба 20x20x2,1.08,65\n2:Труба 40x40x2,2.33,130\n3:Труба 60x40x2,2.96,170")
    
    prices = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            k, data = line.strip().split(":")
            name, w, p = data.split(",")
            prices[k] = {"name": name, "weight": float(w), "price": float(p)}
    return prices

# --- 2. ИНЖЕНЕРНОЕ ЯДРО (Геометрия + 3D точки) ---
def calculate_complex(L, W, H, step=500):
    levels = int(H / step)
    # Список деталей
    details = [
        {"item": "Стойка", "qty": 4, "size": H},
        {"item": "Длинная перемычка", "qty": levels * 2, "size": L},
        {"item": "Короткая перемычка", "qty": levels * 2, "size": W}
    ]
    # Генерируем 8 ключевых точек для 3D (углы каркаса)
    nodes = [
        (0,0,0), (L,0,0), (L,W,0), (0,W,0),
        (0,0,H), (L,0,H), (L,W,H), (0,W,H)
    ]
    return details, nodes

# --- 3. ГЛАВНЫЙ ЦИКЛ ---
print("--- RomanDev Engineering Suite v3.0 запущен ---")

while True:
    metal_base = load_prices()
    print("\n" + "="*50)
    user_input = input("Введите L, W, H (мм) или 'выход': ")
    if user_input.lower() == 'выход': break
    
    try:
        L, W, H = map(float, user_input.split(','))
        
        print("\nВЫБЕРИТЕ МЕТАЛЛ:")
        for k, v in metal_base.items(): print(f"{k}. {v['name']}")
        choice = input("Номер: ")
        sel = metal_base.get(choice, metal_base["2"])
        
        # РАСЧЕТЫ
        details, nodes = calculate_complex(L, W, H)
        total_m = sum((d['qty'] * d['size']) / 1000 for d in details)
        
        # ЭКОНОМИКА (Путь 1)
        mat_cost = total_m * sel['price']
        consumables = mat_cost * 0.10  # 10% на расходники (электроды, диски)
        work_cost = mat_cost * 0.40    # 40% за работу (сварка, зачистка)
        total_price = mat_cost + consumables + work_cost
        
        # ВЫВОД НА ЭКРАН
        res = f"\n📊 ПОЛНАЯ СМЕТА ({sel['name']}):"
        res += f"\n- Металл: {mat_cost:.0f} грн ({total_m:.2f} м)"
        res += f"\n- Расходники: {consumables:.0f} грн"
        res += f"\n- Работа (сварка/сборка): {work_cost:.0f} грн"
        res += f"\n🔥 ИТОГО К ОПЛАТЕ: {total_price:.0f} грн"
        print(res)

        # ЭКСПОРТ ДАННЫХ (Путь 2 и 3)
        with open("project_data.txt", "w") as f:
            f.write(f"MODEL:{L},{W},{H}\n")
            f.write(f"NODES:{nodes}\n") # Это задел для 3D-скрипта в Blender
            f.write(f"TOTAL_PRICE:{total_price}\n")
        
        print("\n💾 Данные для 3D и Веб сохранены в project_data.txt")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        