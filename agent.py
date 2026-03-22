import os
from datetime import datetime

# --- 1. ИНЖЕНЕРНОЕ ЯДРО (Расчет деталей) ---
def calculate_frame(L, W, H, step=500):
    levels = int(H / step)
    cut_list = [
        {"item": "Стойка (вертикаль)", "qty": 4, "size": H},
        {"item": "Перемычка (длина)", "qty": levels * 2, "size": L},
        {"item": "Перемычка (ширина)", "qty": levels * 2, "size": W}
    ]
    return cut_list

# --- 2. БАЗА ДАННЫХ МЕТАЛЛОПРОКАТА ---
# Вес взят средний для толщины стенки 2мм (кроме 80х80)
metal_base = {
    "1": {"name": "Труба 20х20х2", "weight": 1.08, "price": 60},
    "2": {"name": "Труба 25х25х2", "weight": 1.39, "price": 75},
    "3": {"name": "Труба 30х30х2", "weight": 1.70, "price": 95},
    "4": {"name": "Труба 40х20х2", "weight": 1.70, "price": 95},
    "5": {"name": "Труба 40х40х2", "weight": 2.33, "price": 125},
    "6": {"name": "Труба 50х50х2", "weight": 2.96, "price": 160},
    "7": {"name": "Труба 60х30х2", "weight": 2.64, "price": 145},
    "8": {"name": "Труба 60х40х2", "weight": 2.96, "price": 165},
    "9": {"name": "Труба 80х80х3", "weight": 7.00, "price": 380}
}

# --- 3. ГЛАВНЫЙ ЦИКЛ ---
print("--- RomanDev AI: Профессиональный Инженерный Агент ---")

while True:
    print("\n" + "="*40)
    user_input = input("Введите габариты (Длина, Ширина, Высота в мм) или 'выход': ")
    
    if user_input.lower() == 'выход':
        print("До связи! Проект сохранен.")
        break
    
    try:
        L, W, H = map(float, user_input.split(','))
        
        # ВЫБОР ТИПА ТРУБЫ
        print("\nДОСТУПНЫЙ МЕТАЛЛОПРОКАТ:")
        for k, v in metal_base.items():
            print(f"{k}. {v['name']} ({v['price']} грн/м)")
            
        m_choice = input("\nВыберите номер трубы (по умолчанию 40х40): ")
        selected = metal_base.get(m_choice, metal_base["5"])
        
        # Расчет
        details = calculate_frame(L, W, H)
        W_M = selected["weight"]
        P_M = selected["price"]
        M_NAME = selected["name"]
        
        total_m = 0
        output = f"\n--- ЗАКАЗ: {M_NAME} | РАЗМЕР: {L}x{W}x{H} мм ---\n"
        
        for d in details:
            line_m = (d['qty'] * d['size']) / 1000
            total_m += line_m
            output += f"• {d['item']}: {d['qty']} шт по {d['size']} мм ({line_m:.2f} м)\n"

        total_w = total_m * W_M
        total_c = total_m * P_M
        
        footer = f"\n📊 ИТОГИ РАСЧЕТА:"
        footer += f"\n- Общий метраж: {total_m:.2f} м.п."
        footer += f"\n- Вес конструкции: {total_w:.1f} кг"
        footer += f"\n- Сметная стоимость: {total_c:.0f} грн"
        footer += f"\n{'-'*40}\n"
        
        print(output + footer)
        
        # ЗАПИСЬ В ФАЙЛ
        with open("SMETA.txt", "a", encoding="utf-8") as f:
            f.write(f"\nДАТА: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(output + footer)
        
        print("✅ Расчет успешно добавлен в SMETA.txt")

    except ValueError:
        print("❌ Ошибка! Нужно 3 числа через запятую. Пример: 2000, 800, 1200")
        