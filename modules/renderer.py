def generate_3d_model(L, W, H, details, t=40, filename="frame_model.obj"):
    all_v = []
    all_f = []

    def add_box(x, y, z, dx, dy, dz):
        start_v = len(all_v) + 1
        v = [(x,y,z), (x+dx,y,z), (x+dx,y+dy,z), (x,y+dy,z),
             (x,y,z+dz), (x+dx,y,z+dz), (x+dx,y+dy,z+dz), (x,y+dy,z+dz)]
        f = [(1,2,3,4), (5,6,7,8), (1,5,6,2), (2,6,7,3), (3,7,8,4), (4,8,5,1)]
        all_v.extend(v)
        for face in f:
            all_f.append([idx + start_v - 1 for idx in face])

    # Стойки
    for px, py in [(0,0), (L-t,0), (L-t,W-t), (0,W-t)]:
        add_box(px, py, 0, t, t, H)

    # Поиск количества уровней из деталей
    qty_l = 0
    for d in details:
        if "L" in d['item']: qty_l = d['qty']
    
    levels = int(qty_l / 2)
    step = H / levels if levels > 0 else H

    # Рисуем горизонтальные рамки на каждом уровне
    for i in range(levels + 1):
        z = i * step
        if z > H - t: z = H - t
        add_box(t, 0, z, L-2*t, t, t)
        add_box(t, W-t, z, L-2*t, t, t)
        add_box(0, t, z, t, W-2*t, t)
        add_box(L-t, t, z, t, W-2*t, t)

    with open(filename, "w") as f:
        for v in all_v: f.write(f"v {v[0]/1000:.4f} {v[1]/1000:.4f} {v[2]/1000:.4f}\n")
        for face in all_f: f.write(f"f {' '.join(map(str, face))}\n")
    return True
