import os
from fpdf import FPDF
from deep_translator import GoogleTranslator

class SmartReport(FPDF):
    def __init__(self, target_lang='ru'):
        super().__init__()
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source='auto', target=target_lang)
        
        # ПРОВЕРКА ШРИФТА (Исправлено)
        # Убедись, что файл в папке fonts называется именно arial.ttf (маленькими буквами)
        font_path = os.path.join('fonts', 'arial.ttf') 
        
        if os.path.exists(font_path):
            self.add_font('CustomArial', '', font_path)
            self.font_name = 'CustomArial'
            print("✅ Шрифт Arial успешно найден и подключен!")
        else:
            self.font_name = 'Arial'
            print("⚠️ Файл fonts/arial.ttf не найден! Кириллица может не отобразиться.")

    def create_pdf(self, data, filename):
        self.add_page()
        self.set_font(self.font_name, '', 16)
        
        # Перевод заголовка
        title = self.translator.translate("Technical Engineering Report")
        self.cell(0, 15, title, ln=True, align='C')
        self.ln(10)

        # Таблица данных
        self.set_font(self.font_name, '', 12)
        for key, value in data.items():
            translated_key = self.translator.translate(key)
            self.cell(0, 10, f"{translated_key}: {value}", ln=True)

        # Сохранение в папку reports
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        full_path = os.path.join('reports', filename)
        self.output(full_path)
        print(f"🚀 Успех! Отчет создан: {full_path}")

# Блок запуска программы
if __name__ == "__main__":
    # Тестовые данные для твоего будущего VR-мира
    my_data = {
        "Project": "Solarpunk City Concept",
        "Engineer": "Roman",
        "Estimated Assets": "45 models",
        "Status": "Waiting for SSD upgrade"
    }

    report = SmartReport(target_lang='ru')
    report.create_pdf(my_data, "test_report.pdf")
    