def optimize_cutting(required_parts, stock_length=6000, kerf=3):
    """
    Алгоритм оптимальной нарезки (Bin Packing).
    kerf — толщина реза болгарки (3 мм).
    """
    # Сортируем детали от больших к меньшим для лучшей упаковки
    parts = sorted(required_parts, reverse=True)
    
    # Список труб (хлыстов). Каждая труба — это словарь с остатком и списком деталей.
    bins = []

    for part in parts:
        placed = False
        # Пробуем положить деталь в уже начатую трубу
        for b in bins:
            if b["rem"] >= (part + kerf):
                b["cuts"].append(part)
                b["rem"] -= (part + kerf)
                placed = True
                break
        
        # Если в старые не влезло — открываем новую 6-метровую трубу
        if not placed:
            bins.append({
                "cuts": [part],
                "rem": stock_length - part - kerf
            })
    
    return bins
