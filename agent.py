import os
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 1. Настройки
try:
    import openpyxl
except ImportError:
    os.system('pip install openpyxl')

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- НОВАЯ ФУНКЦИЯ: ЖУРНАЛ СОБЫТИЙ ---
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Режим 'a' (append) значит "добавить в конец", не удаляя старое
    with open("history.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# 2. ФУНКЦИИ-УМЕНИЯ

def create_excel_report(user_text):
    try:
        lines = user_text.split(';')
        data = []
        total_sum = 0
        
        for line in lines:
            columns = [item.strip() for item in line.split(',')]
            if len(columns) == 3:
                name = columns[0]
                try:
                    quantity = float(columns[1])
                    price = float(columns[2])
                    cost = quantity * price
                    total_sum += cost
                    data.append({"Наименование": name, "Кол-во": quantity, "Цена": price, "Всего": cost})
                except ValueError:
                    continue
        
        if not data:
            return "❌ Нет данных для записи."

        df = pd.DataFrame(data)
        final_row = pd.DataFrame([{"Наименование": "ИТОГО:", "Всего": total_sum}])
        df = pd.concat([df, final_row], ignore_index=True)

        current_date = datetime.now().strftime("%d-%m-%Y_%H-%M")
        file_name = f"Smeta_{current_date}.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        
        # ЗАПИСЫВАЕМ В ЖУРНАЛ
        log_event(f"Создана смета {file_name} на сумму {total_sum} грн.")
        
        return f"✅ Смета создана: '{file_name}'. Сумма: {total_sum} грн."
    except Exception as e:
        log_event(f"ОШИБКА: {e}")
        return f"❌ Ошибка: {e}"

# 3. ГЛАВНАЯ ЛОГИКА
model = genai.GenerativeModel('gemini-1.5-flash')

def start_agent():
    print("\n" + "="*45)
    print("--- RomanDev AI: Система с Журналом Событий ---")
    print("="*45 + "\n")
    log_event("Агент запущен пользователем RomanDev") # Фиксируем запуск
    
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ['выход', 'exit']:
            log_event("Агент остановлен")
            break
        
        if "запиши в таблицу" in user_input.lower():
            raw_data = input("Данные (Товар, Кол-во, Цена; ...): ")
            print(f"Агент: {create_excel_report(raw_data)}")
            continue

        try:
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    start_agent()
    



