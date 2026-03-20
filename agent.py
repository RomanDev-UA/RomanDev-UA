import os
import google.generativeai as genai
import pandas as pd
from datetime import datetime  # Добавляем работу с датами
from dotenv import load_dotenv

# 1. Настройки и библиотеки
try:
    import openpyxl
except ImportError:
    os.system('pip install openpyxl')

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. ФУНКЦИИ-УМЕНИЯ

def create_excel_report(user_text):
    try:
        lines = user_text.split(';')
        data = []
        total_sum = 0
        
        for line in lines:
            columns = [item.strip() for item in line.split(',')]
            
            # Проверяем, что в строке 3 колонки
            if len(columns) == 3:
                name = columns[0]
                try:
                    # Защита: пробуем превратить в числа. Если там текст - уйдем в except
                    quantity = float(columns[1])
                    price = float(columns[2])
                    cost = quantity * price
                    total_sum += cost
                    
                    data.append({
                        "Наименование": name,
                        "Количество": quantity,
                        "Цена за ед.": price,
                        "Всего": cost
                    })
                except ValueError:
                    print(f"⚠️ Пропускаю строку '{line}': проверьте числа (используйте точку вместо запятой в числах)")
                    continue
        
        if not data:
            return "❌ Ошибка: не нашел данных для расчета. Формат: Товар, Кол-во, Цена;"

        df = pd.DataFrame(data)
        
        # Добавляем строку ИТОГО
        final_row = pd.DataFrame([{"Наименование": "ИТОГО:", "Всего": total_sum}])
        df = pd.concat([df, final_row], ignore_index=True)

        # АВТО-ДАТА: Создаем имя файла типа Smeta_20-03-2026.xlsx
        current_date = datetime.now().strftime("%d-%m-%Y_%H-%M")
        file_name = f"Smeta_{current_date}.xlsx"
        
        df.to_excel(file_name, index=False, engine='openpyxl')
        return f"✅ Смета создана автоматически: '{file_name}'. Сумма: {total_sum} грн."
    except Exception as e:
        return f"❌ Критическая ошибка: {e}"

# 3. ГЛАВНАЯ ЛОГИКА
model = genai.GenerativeModel('gemini-1.5-flash')

def start_agent():
    print("\n" + "="*45)
    print("--- RomanDev AI: Умная Смета (с авто-датой) ---")
    print("="*45 + "\n")
    
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ['выход', 'exit']: break
        
        # Упрощенная команда: теперь не надо вводить имя файла вручную!
        if "запиши в таблицу" in user_input.lower():
            print("Агент: Введите данные (Формат: Товар, Кол-во, Цена; ...)")
            raw_data = input("Данные: ")
            print(f"Агент: {create_excel_report(raw_data)}")
            continue

        try:
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    start_agent()
    



