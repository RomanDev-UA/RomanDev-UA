import os
from datetime import datetime
from modules.optimizer import optimize_cutting
from modules.renderer import generate_3d_model

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
    return [{"item":"Стойка","qty":4,"size":H}, {"item":"L","qty":levels*2,"size":L}, {"item":"W","qty":levels*2,"size":W}]

print("--- RomanDev Engineering v4.7 ---")

while True:
    metal_base = load_prices()
    inp = input("\nВведите L, W, H (мм) через запятую (напр. 1500,800,2000): ")
    if inp.lower() in ['выход', 'exit']: break
    
    try:
        L, W, H = map(float, inp.split(','))
        
        # Поиск металла
        search = input("Какой профиль (напр. 40): ").lower()
        filtered = {k: v for k, v in metal_base.items() if search in v['name'].lower() or search == 'все'}
        if not filtered: filtered = metal_base
        
        for k, v in filtered.items(): print(f"{k}. {v['name']}")
        choice = input("Номер: ")
        sel = filtered.get(choice, list(filtered.values())[0])

        # Расчет нарезки
        details = calculate_frame(L, W, H)
        all_p = [d['size'] for d in details for _ in range(int(d['qty']))]
        bins = optimize_cutting(all_p, 6000, 3)

        # 3D Рендер (Толщина t берется из названия или ставится 40)
        t_val = 40
        for word in sel['name'].replace('х',' ').split():
            if word.isdigit():
                t_val = float(word)
                break

        if generate_3d_model(L, W, H, t_val):
            print(f"📦 3D-модель сохранена в frame_model.obj (Профиль: {int(t_val)}мм)")

        print(f"💰 Итого: {len(bins)*6*sel['price']:.0f} грн. (Труб: {len(bins)} шт)")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
