def generate_3d_model(L, W, H, t=40, filename="frame_model.obj"):
    """ Генерирует 3D модель каркаса из объемных балок. """
    all_v = []
    all_f = []

    def add_box(x, y, z, dx, dy, dz):
        start_v = len(all_v) + 1 # В OBJ индексы начинаются с 1
        # 8 вершин куба
        v = [
            (x, y, z), (x+dx, y, z), (x+dx, y+dy, z), (x, y+dy, z),
            (x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)
        ]
        # 6 граней (полигонов)
        f = [
            (1,2,3,4), (5,6,7,8), (1,5,6,2), (2,6,7,3), (3,7,8,4), (4,8,5,1)
        ]
        all_v.extend(v)
        for face in f:
            all_f.append([idx + start_v - 1 for idx in face])

    # Стойки
    for px, py in [(0,0), (L-t,0), (L-t,W-t), (0,W-t)]:
        add_box(px, py, 0, t, t, H)

    # Горизонтальные перемычки (низ и верх)
    for pz in [0, H-t]:
        add_box(t, 0, pz, L-2*t, t, t)     # Длинные L
        add_box(t, W-t, pz, L-2*t, t, t)
        add_box(0, t, pz, t, W-2*t, t)     # Короткие W
        add_box(L-t, t, pz, t, W-2*t, t)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# RomanDev Solid Model\n")
            for v in all_v:
                # Масштаб мм -> метры
                f.write(f"v {v[0]/1000:.4f} {v[1]/1000:.4f} {v[2]/1000:.4f}\n")
            for face in all_f:
                f.write(f"f {' '.join(map(str, face))}\n")
        return True
    except:
        return False
    