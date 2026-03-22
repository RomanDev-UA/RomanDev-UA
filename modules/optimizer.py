def optimize_cutting(required_parts, stock_length=6000, kerf=3):
    """
    kerf=3 — это толщина диска болгарки (3 мм на каждый рез)
    """
    parts = sorted(required_parts, reverse=True)
    bins = []

    for part in parts:
        placed = False
        for i in range(len(bins)):
            # Проверяем: влезет ли деталь + запас на рез
            if bins[i] >= (part + kerf):
                bins[i] -= (part + kerf)
                placed = True
                break
        
        if not placed:
            # От новой трубы отнимаем деталь и один рез
            bins.append(stock_length - part - kerf)
    
    return len(bins), bins
