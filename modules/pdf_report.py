from fpdf import FPDF
from datetime import datetime
import os

def create_pdf_report(L, W, H, mat_name, cost, weight, bins, advice, waste):
    pdf = FPDF()
    pdf.add_page()
    
    # Подключение шрифта (Кириллица)
    font_path = "arial.ttf"
    if not os.path.exists(font_path):
        font_path = os.path.join("modules", "arial.ttf")
    
    if os.path.exists(font_path):
        pdf.add_font('Arial', '', font_path, uni=True)
        pdf.set_font('Arial', '', 12)
        font_b = 'Arial'
    else:
        pdf.set_font("Arial", size=12)
        font_b = "Arial"

    # Заголовок
    pdf.set_font(font_b, size=16)
    pdf.cell(200, 10, txt="ИНЖЕНЕРНЫЙ ОТЧЕТ: RomanDev Suite v5.0", ln=True, align='C')
    pdf.ln(10)
    
    # Данные объекта
    pdf.set_font(font_b, size=11)
    pdf.cell(200, 10, txt=f"Дата расчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Габариты объекта: {int(L)} x {int(W)} x {int(H)} мм", ln=True)
    pdf.cell(200, 10, txt=f"Материал: {mat_name}", ln=True)
    pdf.ln(5)
    
    # Технические показатели
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font(font_b, size=12)
    pdf.cell(0, 10, txt="ТЕХНИКО-ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ", ln=True, fill=True)
    pdf.set_font(font_b, size=10)
    
    pdf.cell(90, 8, txt="Итоговая стоимость:", border='B')
    pdf.cell(90, 8, txt=f"{cost:.0f} грн", border='B', ln=True)
    
    pdf.cell(90, 8, txt="Общий вес:", border='B')
    pdf.cell(90, 8, txt=f"{weight:.1f} кг", border='B', ln=True)
    
    pdf.cell(90, 8, txt="Запас/Отходы:", border='B')
    pdf.cell(90, 8, txt=f"{waste:.1f}%", border='B', ln=True)
    pdf.ln(5)
    
    # Инженерные рекомендации
    pdf.set_font(font_b, size=11)
    pdf.cell(0, 10, txt="РЕКОМЕНДАЦИИ ПО ТЕХНОЛОГИИ:", ln=True)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 10, txt=f"Анализ: {advice}", border=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Специфика: ТРУБА или ЛИСТ
    # Если bins — это словарь (иногда оптимизаторы так делают), берем только список нарезки
    actual_bins = bins.get('bins', bins) if isinstance(bins, dict) else bins

    if actual_bins and isinstance(actual_bins, list) and len(actual_bins) > 0:
        pdf.set_font(font_b, size=12)
        pdf.cell(0, 10, txt="СХЕМА РАСКРОЯ ХЛЫСТОВ (по 6000 мм):", ln=True)
        pdf.set_font(font_b, size=9)
        
        for i, b in enumerate(actual_bins):
            # Проверяем, что b — это список, и фильтруем только числа
            if isinstance(b, list):
                # Оставляем только те элементы, которые являются числами (int или float)
                clean_parts = [str(int(x)) for x in b if isinstance(x, (int, float))]
                details_str = " + ".join(clean_parts)
                
                # Считаем остаток (только числовые значения)
                numeric_b = [x for x in b if isinstance(x, (int, float))]
                used_space = sum(numeric_b) + (max(0, len(numeric_b)-1) * 3)
                rem = 6000 - used_space
                
                pdf.cell(0, 7, txt=f"Хлыст {i+1}: [{details_str}] | Остаток: {int(rem)} мм", ln=True)
    else:
        # Секция для ЛИСТА
        area = (float(L) * float(W)) / 1_000_000
        pdf.set_font(font_b, size=12)
        pdf.cell(0, 10, txt="ДАННЫЕ ПО ЛИСТОВОМУ МАТЕРИАЛУ:", ln=True)
        pdf.set_font(font_b, size=10)
        pdf.cell(0, 7, txt=f"Расчетная площадь покрытия: {area:.2f} м2", ln=True)
        pdf.cell(0, 7, txt="Примечание: Расчет веса произведен исходя из общей площади.", ln=True)
    
    # Сохранение
    filename = "Order_Report.pdf"
    pdf.output(filename)
    return filename
