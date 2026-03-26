import tkinter as tk
from tkinter import ttk, messagebox
import re
# Импортируем твои рабочие модули
from modules.optimizer import optimize_cutting
from modules.renderer import generate_3d_model
from modules.pdf_report import create_pdf_report
import os

class RomanDevApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RomanDev Engineering Suite v6.0")
        self.root.geometry("500x600")
        
        self.prices = self.load_prices()
        self.create_widgets()

    def load_prices(self):
        prices = {}
        if os.path.exists("prices.txt"):
            with open("prices.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, data = line.strip().split(":")
                        name, w, p = data.split(",")
                        prices[name] = {"weight": float(w), "price": float(p)}
        return prices

    def create_widgets(self):
        # Поля ввода габаритов
        tk.Label(self.root, text="Габариты каркаса (мм):", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame_inputs = tk.Frame(self.root)
        frame_inputs.pack()
        
        self.ent_l = self.make_entry(frame_inputs, "Длина (L):", "2000")
        self.ent_w = self.make_entry(frame_inputs, "Ширина (W):", "1500")
        self.ent_h = self.make_entry(frame_inputs, "Высота (H):", "1000")

        # Выбор металла
        tk.Label(self.root, text="Выберите материал:").pack(pady=5)
        self.combo_metal = ttk.Combobox(self.root, values=list(self.prices.keys()), width=45)
        self.combo_metal.pack(pady=5)
        if list(self.prices.keys()): self.combo_metal.current(0)

        # Кнопка Расчета
        self.btn_calc = tk.Button(self.root, text="РАССЧИТАТЬ И СОЗДАТЬ ОТЧЕТ", 
                                 bg="green", fg="white", font=('Arial', 10, 'bold'),
                                 command=self.run_calculation)
        self.btn_calc.pack(pady=20, fill='x', padx=50)

        # Текстовое поле для лога
        self.txt_log = tk.Text(self.root, height=10, width=55)
        self.txt_log.pack(pady=10)

    def make_entry(self, parent, label, default):
        f = tk.Frame(parent)
        f.pack(side='left', padx=5)
        tk.Label(f, text=label).pack()
        e = tk.Entry(f, width=10)
        e.insert(0, default)
        e.pack()
        return e

    def run_calculation(self):
        try:
            L, W, H = float(self.ent_l.get()), float(self.ent_w.get()), float(self.ent_h.get())
            mat_name = self.combo_metal.get()
            sel = self.prices[mat_name]

            # Логика как в agent.py
            details = [
                {"item": "Стойка", "qty": 4, "size": H},
                {"item": "Перемычка L", "qty": 4, "size": L},
                {"item": "Перемычка W", "qty": 4, "size": W}
            ]
            all_pieces = [d['size'] for d in details for _ in range(int(d['qty']))]
            
            # Если не лист (простая проверка по названию)
            bins = []
            if "Труба" in mat_name:
                bins = optimize_cutting(all_pieces, 6000, kerf=3)
                total_len = len(bins) * 6
            else:
                total_len = (L * W * 2) / 1000 # Пример для листов

            total_cost = total_len * sel['price']
            total_weight = total_len * sel['weight']
            
            # Физика сварки
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", mat_name)
            wall = float(nums[-1]) if nums else 2.0
            advice = "НИЗКИЙ риск" if wall > 2 else "КРИТИЧЕСКИЙ нагрев!"

            # Генерация файлов
            generate_3d_model(L, W, H, details)
            create_pdf_report(L, W, H, mat_name, total_cost, total_weight, bins, advice, 5.0)

            # Вывод в лог
            self.txt_log.delete(1.0, tk.END)
            self.txt_log.insert(tk.END, f"Проект: {mat_name}\n")
            self.txt_log.insert(tk.END, f"Итого вес: {total_weight:.1f} кг\n")
            self.txt_log.insert(tk.END, f"Цена: {total_cost:.0f} грн\n")
            self.txt_log.insert(tk.END, f"Совет: {advice}\n")
            messagebox.showinfo("Успех", "PDF отчет и 3D модель созданы!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Проверь данные: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RomanDevApp(root)
    root.mainloop()
    