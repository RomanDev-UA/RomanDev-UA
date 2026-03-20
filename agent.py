import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

# 1. Настройки
try:
    import openpyxl
except ImportError:
    os.system('pip install openpyxl')

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. ФУНКЦИИ-УМЕНИЯ

def create_folders(project_name):
    folders = [f"{project_name}/code", f"{project_name}/data", f"{project_name}/docs"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    return f"✅ Структура проекта '{project_name}' создана!"

def create_excel_report(filename, user_text):
    try:
        lines = user_text.split(';')
        data = []
        total_sum = 0 # Переменная для хранения общей суммы
        
        for line in lines:
            columns = [item.strip() for item in line.split(',')]
            
            # Проверяем, что у нас есть Название, Кол-во и Цена (3 колонки)
            if len(columns) >= 3:
                name = columns[0]
                try:
                    quantity = float(columns[1]) # Превращаем текст в число
                    price = float(columns[2])    # Превращаем текст в число
                    cost = quantity * price      # Считаем стоимость позиции
                    total_sum += cost            # Прибавляем к общей сумме
                    
                    data.append({
                        "Наименование": name,
                        "Количество": quantity,
                        "Цена за ед.": price,
                        "Всего": cost
                    })
                except ValueError:
                    continue # Если вместо числа ввели текст, пропускаем строку
        
        if not data:
            return "❌ Ошибка: используй формат 'Товар, Кол-во, Цена; ...'"

        # Создаем таблицу
        df = pd.DataFrame(data)
        
        # Добавляем пустую строку и строку "ИТОГО" в конец
        final_row = pd.DataFrame([{"Наименование": "ИТОГО:", "Всего": total_sum}])
        df = pd.concat([df, final_row], ignore_index=True)

        file_name = f"{filename}.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        
        return f"✅ Смета '{file_name}' готова! Сумма: {total_sum} грн."
    except Exception as e:
        return f"❌ Ошибка: {e}"

# 3. ГЛАВНАЯ ЛОГИКА
model = genai.GenerativeModel('gemini-1.5-flash')

def start_agent():
    print("\n" + "="*40)
    print("--- RomanDev AI: Калькулятор Смет v3.0 ---")
    print("="*40 + "\n")
    
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ['выход', 'exit']: break
        
        if "создай проект" in user_input.lower():
            name = user_input.split()[-1]
            print(f"Агент: {create_folders(name)}")
            continue

        if "запиши в таблицу" in user_input.lower():
            fname = input("Имя файла: ")
            print("Введите данные (Формат: Товар, Кол-во, Цена; ...)")
            raw_data = input("Данные: ")
            print(f"Агент: {create_excel_report(fname, raw_data)}")
            continue

        try:
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    start_agent()
    



