import os
from fpdf import FPDF
from datetime import datetime

def create_pdf_report(L, W, H, metal_name, cost, weight, bins, filename="Order_Report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    
    # ПРОВЕРКА ВСЕХ ВАРИАНТОВ ИМЕНИ
    possible_names = ["arial.ttf", "Arial.ttf", "ARIAL.TTF"]
    font_path = None
    
    for name in possible_names:
        if os.path.exists(name):
            font_path = name
            break

    if font_path:
        # ШРИФТ НАЙДЕН - ВКЛЮЧАЕМ РУССКИЙ
        pdf.add_font('ArialRus', '', font_path)
        pdf.set_font('ArialRus', '', 12)
        
        title = "RomanDev Engineering - Отчет по заказу"
        date_text = f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        dim_text = f"Размеры: {int(L)}x{int(W)}x{int(H)} мм"
        mat_text = f"Материал: {metal_name}"
        total_text = f"ИТОГО: {cost:.0f} грн"
        weight_text = f"Общий вес: {weight:.1f} кг"
        cut_text_header = "Карта раскроя (6м):"
        pipe_label = "Труба"
        rem_label = "Остаток"
    else:
        # ШРИФТ НЕ НАЙДЕН - АНГЛИЙСКИЙ
        pdf.set_font("Helvetica", size=12)
        title = "Order Report (Font not found)"
        date_text = f"Date: {datetime.now().strftime('%d.%m.%Y')}"
        dim_text = f"Dimensions: {int(L)}x{int(W)}x{int(H)}"
        mat_text = "Material: Selected Profile"
        total_text = f"TOTAL: {cost:.0f} UAH"
        weight_text = f"Weight: {weight:.1f} kg"
        cut_text_header = "Cutting Plan:"
        pipe_label = "Pipe"
        rem_label = "Rem"

    # --- ПЕЧАТЬ В PDF ---
    pdf.set_font(size=16)
    pdf.cell(0, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font(size=12)
    pdf.cell(0, 10, txt=date_text, ln=True)
    pdf.cell(0, 10, txt=dim_text, ln=True)
    pdf.cell(0, 10, txt=mat_text, ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 10, txt=total_text, ln=True)
    pdf.cell(0, 10, txt=weight_text, ln=True)
    pdf.ln(10)
    
    pdf.cell(0, 10, txt=cut_text_header, ln=True)
    for i, b in enumerate(bins, 1):
        cuts = " + ".join([f"{int(c)}mm" for c in b["cuts"]])
        pdf.cell(0, 8, f"{pipe_label} #{i}: [{cuts}] | {rem_label}: {int(b['rem'])}mm", ln=True)

    pdf.output(filename)
    return True
