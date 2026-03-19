import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

# 1. АВТОМАТИЧЕСКАЯ НАСТРОЙКА (Установка поддержки Excel, если её нет)
try:
    import openpyxl
except ImportError:
    os.system('pip install openpyxl')

# 2. ПОДКЛЮЧЕНИЕ К GEMINI
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 3. ФУНКЦИИ-УМЕНИЯ РОМАНА (Инструменты агента)

def create_folders(project_name):
    """Создает структуру папок для нового проекта"""
    folders = [
        f"{project_name}/code", 
        f"{project_name}/data", 
        f"{project_name}/docs"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    return f"✅ Папки для проекта '{project_name}' успешно созданы!"

def create_excel_report(filename, user_text):
    """Превращает текст в настоящий Excel-файл (.xlsx)"""
    try:
        # Разбиваем текст на строки (разделитель ;)
        lines = user_text.split(';')
        data = []
        for line in lines:
            # Разбиваем на колонки (разделитель ,)
            columns = [item.strip() for item in line.split(',')]
            if len(columns) >= 2:
                data.append({
                    "Наименование": columns[0], 
                    "Значение/Цена": columns[1]
                })
        
        if not data:
            return "❌ Ошибка: используй формат 'Товар, Цена; Товар, Цена'"

        # Создаем таблицу
        df = pd.DataFrame(data)
        
        # Сохраняем как НАСТОЯЩИЙ EXCEL (.xlsx)
        file_name = f"{filename}.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')
        
        return f"✅ Настоящий Excel-файл '{file_name}' готов! Записано строк: {len(data)}"
    except Exception as e:
        return f"❌ Ошибка при создании Excel: {e}"

# 4. ГЛАВНАЯ ЛОГИКА АГЕНТА
model = genai.GenerativeModel('gemini-1.5-flash')

def start_agent():
    print("\n" + "="*40)
    print("--- RomanDev AI: Автоматизация v2.0 ---")
    print("Доступные команды: 'создай проект', 'запиши в таблицу'")
    print("="*40 + "\n")
    
    while True:
        user_input = input("Вы: ")
        
        # Выход из программы
        if user_input.lower() in ['выход', 'exit', 'quit']:
            print("Агент: До связи, Роман! Успехов в коде.")
            break
        
        # Проверка пустых сообщений
        if not user_input.strip():
            continue

        # КОМАНДА 1: СОЗДАНИЕ ПАПОК
        if "создай проект" in user_input.lower():
            name = user_input.split()[-1]
            print(f"Агент: {create_folders(name)}")
            continue

        # КОМАНДА 2: СОЗДАНИЕ EXCEL
        if "запиши в таблицу" in user_input.lower():
            print("Агент: Введите название файла (без расширения):")
            fname = input("Имя: ")
            print("Агент: Введите данные (Пример: Труба 40мм, 12м; Электроды, 3 пачки):")
            raw_data = input("Данные: ")
            print(f"Агент: {create_excel_report(fname, raw_data)}")
            continue

        # ОБЫЧНЫЙ ЧАТ С AI
        try:
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"Ошибка связи с AI: {e}")

# 5. ЗАПУСК ПРИЛОЖЕНИЯ
if __name__ == "__main__":
    start_agent()
    



