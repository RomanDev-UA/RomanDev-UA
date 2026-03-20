import os
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 1. Настройки и библиотеки
try:
    import openpyxl
except ImportError:
    os.system('pip install openpyxl')

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Функция для автоматического подбора рабочей модели (лечит ошибку 404)
def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name or 'gemini-pro' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# --- ЖУРНАЛ СОБЫТИЙ ---
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                name, qty, price = columns[0], float(columns[1]), float(columns[2])
                cost = qty * price
                total_sum += cost
                data.append({"Наименование": name, "Кол-во": qty, "Цена": price, "Всего": cost})
        
        if not data: return "❌ Ошибка формата."
        
        df = pd.DataFrame(data)
        df = pd.concat([df, pd.DataFrame([{"Наименование": "ИТОГО:", "Всего": total_sum}])], ignore_index=True)
        
        file_name = f"Smeta_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        log_event(f"Создана смета {file_name} на {total_sum} грн.")
        return f"✅ Смета создана: {file_name}. Сумма: {total_sum} грн."
    except Exception as e:
        return f"❌ Ошибка: {e}"

# 3. ГЛАВНАЯ ЛОГИКА
def start_agent():
    print("\n--- RomanDev AI: Исправленная версия 3.3 ---")
    log_event("Агент перезапущен с фиксом модели")
    
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ['выход', 'exit']: break
        
        if "запиши в таблицу" in user_input.lower():
            raw_data = input("Данные (Товар, Кол-во, Цена; ...): ")
            print(f"Агент: {create_excel_report(raw_data)}")
            continue

        try:
            # Теперь здесь используется модель, которую мы проверили при запуске
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"\n❌ Ошибка AI: {e}\nПопробуй обновить страницу или проверить API ключ.")

if __name__ == "__main__":
    start_agent()
    



