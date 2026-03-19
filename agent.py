import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# АВТОПОДБОР МОДЕЛИ:
# Пробуем найти первую попавшуюся рабочую модель из списка разрешенных
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Выбираем flash, если он есть, иначе берем первую из списка
    model_name = next((m for m in available_models if 'flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)
    print(f"✅ Успешно подключена модель: {model_name}")
except Exception as e:
    print(f"❌ Не удалось найти доступные модели: {e}")
    exit()

def start_agent():
    print("\n--- RomanDev AI Agent готов к работе! ---")
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ['выход', 'exit']: break
        if not user_input.strip(): continue
            
        try:
            response = model.generate_content(user_input)
            print(f"\nАгент: {response.text}\n")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    start_agent()
    


