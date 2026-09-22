"""Креслення клітки payload -> fpv/cage-drawings.pdf (3 аркуші A3) і DXF плит -> fpv/cnc/cage_*.dxf

Геометрія — cage_geometry.py; примітиви і штамп — make_sketch.py.
Запуск: python3 fpv/tools/make_cage.py
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cage_geometry as C
import plate_geometry as G
import make_sketch as K
from make_sketch import ln, rect, poly, circ, tx, dim, leader, balloon, horn_shape, INK, DIM, MUT, ACC, CAM, RFC, PWR, SLC
import ezdxf
from ezdxf import units
from ezdxf import path as dxfpath
from shapely.geometry import Polygon

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "cage-drawings.pdf")
CNC = os.path.join(HERE, "..", "cnc")
TOTAL = 3
SHIFT = K.SHIFT
GROUND = K.GROUND
G10C = "#2e7d4f"          # колір склопластику на кресленні
PLATES = C.cage_plates()
PL_NAME = {"horn": "П1", "zr10": "П2", "tray": "П3"}

def mz(v): return K.mz(v)

def sheet(n, title, scale):
    K.sheet(n, TOTAL, title, scale)
    tx(283, 43.5 - 0.0, "", 1)

# ------------------------------------------------------------------ 3D -> вид
def views():
    s = 0.2
    P = lambda x, y: (95 + y * s, 195 + x * s)                  # план: ніс угору
    S = lambda x, z: (235 + x * s, 285.8 + z * s)               # збоку: ніс праворуч
    F = lambda y, z: (235 - y * s, 185.8 + z * s)               # спереду: правий борт ліворуч
    return s, P, S, F

def draw_tubes(view, proj, s):
    """proj(x,y,z)->(px,py) для конкретного виду"""
    for n, a, b, r, mat in C.segments():
        col = INK if mat == "CF" else G10C
        pa, pb = proj(*a), proj(*b)
        if math.dist(pa, pb) < 0.5:
            circ(*pa, r * s + 0.15, 0.35, col, col, 1)
        else:
            ln(*pa, *pb, 2 * r * s, col); ln(*pa, *pb, 0.12, "#ffffff")

def sheet1():
    sheet(1, "Клітка payload · складальне", "1:5")
    s, P, S, F = views()
    tx(24, 274, "КЛІТКА PAYLOAD — СКЛАДАЛЬНЕ КРЕСЛЕННЯ", 12, True)
    tx(24, 268, "чорне — карбон, зелене — склопластик G10 · кольоровий пунктир — payload · сіре — рама фантомом", 7, False, MUT)
    zb, rb, bb = C.zr10_box(), C.rep_box(), C.batt_box(SHIFT)
    # ---------- план ----------
    tx(24, 258, "План", 9, True)
    poly([P(y, x) for x, y in list(G.outline_poly().exterior.coords)[:-1]], 0.25, MUT, dash=(2, 1.5))
    x0, y0 = P(bb["x0"], bb["y0"]); x1, y1 = P(bb["x1"], bb["y1"])
    rect(x0, y0, x1 - x0, y1 - y0, 0.25, PWR, PWR, 0.05, dash=(2, 1.5))
    for key, pl in PLATES.items():
        b = pl["P"]; x0, y0 = P(b["x0"], b["y0"]); x1, y1 = P(b["x1"], b["y1"])
        rect(x0, y0, x1 - x0, y1 - y0, 0.3, INK if pl["mat"] == "CF" else G10C, "#dddddd", 0.5)
    draw_tubes("plan", lambda x, y, z: P(x, y), s)
    for B_, col in ((zb, CAM), (rb, RFC)):
        x0, y0 = P(B_["x0"], B_["y0"]); x1, y1 = P(B_["x1"], B_["y1"])
        rect(x0, y0, x1 - x0, y1 - y0, 0.3, col, col, 0.08, dash=(1.5, 1))
    hr = C.horn_rect(C.HORN["top"] - C.HORN["L"]); x0, y0 = P(hr[0], hr[2]); x1, y1 = P(hr[1], hr[3])
    rect(x0, y0, x1 - x0, y1 - y0, 0.3, RFC, dash=(1.5, 1))
    ya = C.YAGI; L0 = ya["elems"][0][0]
    ln(*P(ya["x"], ya["y"] - L0 / 2), *P(ya["x"], ya["y"] + L0 / 2), 0.5, RFC)
    for sx in (-1, 1):
        for sy in (-1, 1):
            circ(*P(sx * C.LEG_TOP[0], sy * C.LEG_TOP[1]), 1.0, 0.3, INK, "#ffffff", 1)
    tx(24, 250, "НІС ↑", 7, True, INK)
    dim(*P(-300, -C.LEG_BOT[1]), *P(-300, C.LEG_BOT[1]), f"колія {2 * C.LEG_BOT[1]:.0f}", -5, 6.5)
    dim(*P(C.SKID_X[0], -C.LEG_BOT[1]), *P(C.SKID_X[1], -C.LEG_BOT[1]), f"{C.SKID_X[1] - C.SKID_X[0]:.0f}", 5, 6.5)
    dim(*P(C.RAIL_X[0], -C.RAIL_Y), *P(C.RAIL_X[0], C.RAIL_Y), f"{2 * C.RAIL_Y:.0f}", -1.5, 6)
    B = [("Т1", P(-137, -165), (30, 238)), ("Т2", P(-250, -290), (30, 150)), ("Т3", P(250, -C.RAIL_Y), (60, 262)),
         ("Т4", P(C.XBARS["X1"][0], -150), (162, 222)), ("Т5", P(C.XBARS["X2"][0], 150), (162, 196)),
         ("П1", P(-220, 60), (162, 170)), ("П2", P(255, 60), (162, 248)), ("П3", P(80, 165), (162, 209))]
    for n, (ax, ay), (bx, by) in B: balloon(n, ax, ay, bx, by)
    # ---------- вид збоку ----------
    tx(176, 274, "Вид збоку (з правого борту)", 9, True)
    ln(*S(-125, -105), *S(125, -105), 0.8, MUT)
    x0, y0 = S(bb["x0"], bb["z0"]); rect(x0, y0, (bb["x1"] - bb["x0"]) * s, (bb["z1"] - bb["z0"]) * s, 0.25, PWR, PWR, 0.05, dash=(2, 1.5))
    for key, pl in PLATES.items():
        b = pl["P"]; x0, y0 = S(b["x0"], b["z0"]); rect(x0, y0, (b["x1"] - b["x0"]) * s, max((b["z1"] - b["z0"]) * s, 0.5), 0.3, INK, INK, 0.7)
    draw_tubes("side", lambda x, y, z: S(x, z), s)
    horn_shape(C.HORN["x"], C.HORN["top"], C.HORN["top"] - C.HORN["L"], C.HORN["ap"], C.HORN["thr"], s, 235, 285.8, RFC)
    for B_, col in ((zb, CAM), (rb, RFC)):
        x0, y0 = S(B_["x0"], B_["z0"]); rect(x0, y0, (B_["x1"] - B_["x0"]) * s, (B_["z1"] - B_["z0"]) * s, 0.3, col, col, 0.1)
    bx, _ = S(ya["x"], 0)
    ln(bx, S(0, ya["top"])[1], bx, S(0, ya["top"] - ya["boom"])[1], 0.4, RFC, dash=(1.2, 0.8))
    ln(*S(-310, GROUND), *S(310, GROUND), 0.2, MUT)
    dim(*S(305, GROUND), *S(305, -105), f"{-105 - GROUND:.0f}", 0, 6.5)
    dim(*S(C.HORN["x"], C.HORN["top"] - C.HORN["L"]), *S(C.HORN["x"], GROUND), f"{C.HORN['top'] - C.HORN['L'] - GROUND:.0f}", 26, 6)
    B = [("J1", S(115, -115), (297, 272)), ("J2", S(C.J2_X, C.Z_RAIL), (292, 258)), ("J3", S(150, C.LEG_BOT[2]), (292, 190)),
         ("J4", S(C.XBARS["X1"][0], C.Z_XBAR), (250, 268)), ("J5", S(-230, C.Z_RAIL + 8), (178, 262))]
    for n, (ax, ay), (bx2, by2) in B: balloon(n, ax, ay, bx2, by2)
    # ---------- вид спереду ----------
    tx(176, 172, "Вид спереду (з боку носа)", 9, True)
    ln(*F(-125, -105), *F(125, -105), 0.8, MUT)
    x0, _ = F(bb["y1"], 0); rect(x0, F(0, bb["z0"])[1], (bb["y1"] - bb["y0"]) * s, (bb["z1"] - bb["z0"]) * s, 0.25, PWR, PWR, 0.05, dash=(2, 1.5))
    for key, pl in PLATES.items():
        b = pl["P"]; x0, _ = F(b["y1"], 0); rect(x0, F(0, b["z0"])[1], (b["y1"] - b["y0"]) * s, max((b["z1"] - b["z0"]) * s, 0.5), 0.3, INK, INK, 0.7)
    draw_tubes("front", lambda x, y, z: F(y, z), s)
    horn_shape(C.HORN["y"], C.HORN["top"], C.HORN["top"] - C.HORN["L"], C.HORN["ap"], C.HORN["thr"], s, 235, 185.8, RFC, dash=(1.5, 1), fx=-1)
    for B_, col in ((zb, CAM), (rb, RFC)):
        x0, _ = F(B_["y1"], 0); rect(x0, F(0, B_["z0"])[1], (B_["y1"] - B_["y0"]) * s, (B_["z1"] - B_["z0"]) * s, 0.3, col, col, 0.1)
    yb, _ = F(ya["y"], 0)
    ln(yb, F(0, ya["top"])[1], yb, F(0, ya["top"] - ya["boom"])[1], 0.5, RFC)
    for zz, L in C.yagi_elems(): ln(yb - L / 2 * s, F(0, zz)[1], yb + L / 2 * s, F(0, zz)[1], 0.4, RFC)
    ln(*F(310, GROUND), *F(-310, GROUND), 0.2, MUT)
    dim(*F(-C.J2_Y, C.Z_RAIL - 60), *F(-C.RAIL_Y, C.Z_RAIL - 60), "18", -3, 5.5)
    dim(*F(C.YAGI["y"], GROUND), *F(C.YAGI["y"], C.YAGI["top"] - C.YAGI["boom"]), f"{C.YAGI['top'] - C.YAGI['boom'] - GROUND:.0f}", -4, 6)
    tx(*F(-C.YAGI["y"] * 0 + C.YAGI["y"], GROUND - 9), "Ягі", 6.5, True, RFC, "c")
    ang = C.LEG_SPLAY
    tx(*F(C.LEG_BOT[1] - 30, GROUND + 60), f"{ang:.1f}°", 6.5, True, DIM, "c")
    B = [("J6", F(C.YAGI["y"], C.Z_XBAR), (292, 150)), ("J7", F(-C.LEG_BOT[1], C.LEG_BOT[2]), (292, 96))]
    for n, (ax, ay), (bx2, by2) in B: balloon(n, ax, ay, bx2, by2)
    # ---------- таблиці ----------
    X = 305; Y = 272
    tx(X, Y, "Специфікація клітки", 10, True); Y -= 6.5
    tx(X, Y, "Поз.", 6.3, True, MUT); tx(X + 9, Y, "Найменування", 6.3, True, MUT); tx(406, Y, "К-сть", 6.3, True, MUT, "r"); Y -= 1.6
    ln(X, Y, 408, Y, 0.2, MUT); Y -= 4
    rows = [(p, f"{nm} {m} Ø16×14, L {L:.0f}", n) for p, nm, m, L, n in C.tubes()]
    rows += [(PL_NAME[k], f"{pl['title']} {pl['mat']} {pl['t']:.0f} мм", 1) for k, pl in PLATES.items()]
    rows += [(p, f"{nm} · {mat}", n) for p, nm, n, g, mat, _ in C.JOINTS]
    for p, nm, n in rows:
        tx(X + 1, Y, p, 6.6, True); tx(X + 9, Y, nm, 6.6); tx(406, Y, str(n), 6.6, False, INK, "r"); Y -= 4.3
    Y -= 3
    tx(X, Y, "Відстані від Ягі 900 МГц", 8.5, True); Y -= 5.5
    for k, v in sorted(K.RF.items(), key=lambda kv: kv[1]):
        ok = v >= C.LAM4_900
        tx(X, Y, k, 6.6, False, INK if ok else DIM); tx(406, Y, f"{v:.0f} мм" + ("" if ok else " !"), 6.6, True, INK if ok else DIM, "r"); Y -= 4.2
    tx(X, Y - 1, "λ/4 = 83 мм; «!» — перевірити КСХВ", 6, False, MUT)
    # примітки під планом
    Y = 118
    tx(24, Y, "Примітки", 9, True); Y -= 6
    m = C.cage_mass()
    for t in (f"Ягі на x +{C.YAGI['x']:.0f}, y {mz(C.YAGI['y'])} — від рупора {K.RF['рупор']:.0f} мм.",
              "Раніше було 42 мм: металевий рупор розстроював Ягі.",
              "Рейки, поперечки й лоток — G10: поруч з Ягі",
              "карбон не можна, склопластик радіопрозорий.",
              "Вузли J4–J7 — PETG без вуглецевого наповнювача.",
              f"Просвіт: Ягі {C.YAGI['top'] - C.YAGI['boom'] - GROUND:.0f}, рупор {C.HORN['top'] - C.HORN['L'] - GROUND:.0f} мм.",
              f"Маса клітки {m['total']:.0f} г: труби {m['tubes']:.0f}, вузли {m['joints']:.0f},",
              f"плити {m['plates']:.0f}, кріпіж {m['fasteners']:.0f}.",
              f"Батарея — {abs(SHIFT):.0f} мм назад; ЦМ у центрі."):
        tx(24, Y, t, 6.6); Y -= 4.4
    K.c.showPage()

# ------------------------------------------------------------------ аркуш 2
def sheet2():
    sheet(2, "Труби · вузли · маса", "б/м")
    tx(24, 274, "ТРУБИ, ВУЗЛИ, МАСА", 12, True)
    X = 24; Y = 262
    tx(X, Y, "Розкрій труб Ø16×14", 10, True); Y -= 7
    hdr = [("Поз.", 0), ("Найменування", 12), ("Матеріал", 62), ("L різу", 90), ("К-сть", 110), ("Маса", 126)]
    for t, dx in hdr: tx(X + dx, Y, t, 6.8, True, MUT)
    Y -= 2; ln(X, Y, X + 140, Y, 0.2, MUT); Y -= 5
    tot = 0
    for p, nm, mat, L, n in C.tubes():
        g = C.tube_kg_per_m(mat) * L / 1000 * n * 1000; tot += g
        for t, dx in ((p, 0), (nm, 12), ("карбон" if mat == "CF" else "склопластик G10", 62), (f"{L:.0f}", 90), (str(n), 110), (f"{g:.0f} г", 126)):
            tx(X + dx, Y, t, 7.2, dx == 0, INK if mat == "CF" else G10C)
        Y -= 5.4
    tx(X + 90, Y, "разом", 7, True, MUT); tx(X + 126, Y, f"{tot:.0f} г", 7.2, True); Y -= 6
    tx(X, Y, f"Ніжка: між точками вузлів {C.LEG_CC:.1f} мм; торець зупиняється за 8 мм до точки вузла → різ {C.LEG_CUT}.", 6.8); Y -= 4.5
    tx(X, Y, "Рейки, поперечки і лижі проходять крізь вузли — ріжуться в розмір по кресленню.", 6.8); Y -= 4.5
    tx(X, Y, "Склопластик — трубка FR4/G10 намотана, не пултрузійна: пултрузія розшаровується в хомутах.", 6.8, False, DIM)
    # ---- вузли ----
    Y -= 12
    tx(X, Y, "Вузли (друк)", 10, True); Y -= 7
    for t, dx in (("Поз.", 0), ("Назва", 12), ("Матеріал", 62), ("К-сть", 82), ("Маса", 96), ("Опис", 112)):
        tx(X + dx, Y, t, 6.8, True, MUT)
    Y -= 2; ln(X, Y, X + 240, Y, 0.2, MUT); Y -= 5
    for p, nm, n, g, mat, desc in C.JOINTS:
        for t, dx in ((p, 0), (nm, 12), (mat, 62), (str(n), 82), (f"{n * g} г", 96), (desc, 112)):
            tx(X + dx, Y, t, 7, dx == 0)
        Y -= 5.2
    tx(X, Y - 1, "PA-CF — лише для вузлів ніжок (J1–J3): вони ≥ 84 мм від Ягі. Усе, що ближче до антени, — PETG.", 6.8, False, DIM)
    # ---- геометрія ніжки ----
    gx, gy = 300, 205; sc = 0.16
    tx(262, 262, "Геометрія ніжки", 10, True)
    dy_, dz_ = C.LEG_BOT[1] - C.LEG_TOP[1], C.LEG_TOP[2] - C.LEG_BOT[2]
    ln(gx, gy + dz_ * sc / 2, gx + dy_ * sc, gy - dz_ * sc / 2, 1.0, INK)
    ln(gx, gy + dz_ * sc / 2, gx, gy - dz_ * sc / 2, 0.2, MUT, dash=(1.5, 1))
    ln(gx, gy - dz_ * sc / 2, gx + dy_ * sc, gy - dz_ * sc / 2, 0.2, MUT, dash=(1.5, 1))
    tx(gx + 9, gy + dz_ * sc / 2 - 13, f"{C.LEG_SPLAY:.1f}°", 7, True, DIM)
    tx(gx + dy_ * sc / 2, gy - dz_ * sc / 2 - 4, f"{dy_:.0f} вбік", 6.5, False, MUT, "c")
    tx(gx - 2, gy, f"{dz_:.0f}", 6.5, False, MUT, "r")
    tx(gx, gy - dz_ * sc / 2 - 11, "вид спереду", 6.5, False, MUT)
    hx0 = 362
    ln(hx0, gy + dz_ * sc / 2, hx0 + (C.LEG_BOT[0] - C.LEG_TOP[0]) * sc, gy - dz_ * sc / 2, 1.0, INK)
    ln(hx0, gy + dz_ * sc / 2, hx0, gy - dz_ * sc / 2, 0.2, MUT, dash=(1.5, 1))
    tx(hx0 + 3, gy + dz_ * sc / 2 - 7, f"{C.LEG_RAKE:.1f}°", 7, True, DIM)
    tx(hx0, gy - dz_ * sc / 2 - 11, "вид збоку", 6.5, False, MUT)
    tx(262, gy - dz_ * sc / 2 - 20, f"Від вертикалі {C.LEG_TILT:.1f}°. Ніжки розходяться вбік і вперед/назад —", 6.6)
    tx(262, gy - dz_ * sc / 2 - 24.5, "гнізда J1 і J3 друкувати під цей складений кут.", 6.6)
    # ---- деталі зсувів ----
    dx0, dy0 = 272, 118
    tx(262, 138, "Зсув осей у хрестах", 10, True)
    for i, (lbl, off) in enumerate((("J2 ніжка–рейка", 18.0), ("J4 поперечка–рейка", 16.0))):
        cx = dx0 + i * 62
        circ(cx, dy0, 8 * 0.9, 0.4, G10C, "#ffffff", 1); circ(cx + off * 0.9, dy0, 8 * 0.9, 0.4, INK if i == 0 else G10C, "#ffffff", 1)
        dim(cx, dy0 - 10, cx + off * 0.9, dy0 - 10, f"{off:.0f}", -3, 6)
        tx(cx + off * 0.45, dy0 + 11, lbl, 6.6, True, INK, "c")
    tx(262, 96, "Осі не перетинаються — труби проходять одна повз одну,", 6.6)
    tx(262, 91.5, "хомут тримає обидві. Рейки зсунуті на 18 мм всередину від ніжок.", 6.6)
    # ---- маса ----
    m = C.cage_mass()
    tx(24, 88, "Маса клітки і ціна для польоту", 10, True)
    P0, t0, tw0 = K.perf(13.48); P1, t1, tw1 = K.perf(K.AUW)
    rows = [("Труби", f"{m['tubes']:.0f} г"), ("Вузли", f"{m['joints']:.0f} г"), ("Плити П1–П3", f"{m['plates']:.0f} г"),
            ("Кріпіж", f"{m['fasteners']:.0f} г"), ("Разом клітка", f"{m['total']:.0f} г"), ("У бюджеті було", "492 г"),
            ("AUW", f"13.48 → {K.AUW:.2f} кг"), ("Висіння на 1500 м", f"{t0:.1f} → {t1:.1f} хв"), ("T/W на 1500 м", f"{tw0:.2f} → {tw1:.2f}")]
    Y = 80
    for k, v in rows:
        b = k in ("Разом клітка", "Висіння на 1500 м")
        tx(24, Y, k, 7, b, DIM if b else INK); tx(120, Y, v, 7, True, DIM if b else INK, "r"); Y -= 4.8
    tx(130, 80, "Частина різниці, ймовірно, вже сиділа в оцінках", 6.6, False, MUT)
    tx(130, 75.5, "«рупор + кронштейн» і «Ягі + кронштейн».", 6.6, False, MUT)
    tx(130, 71, "Тут узято гірший випадок: вся різниця — нова маса.", 6.6, False, MUT)
    K.c.showPage()

# ------------------------------------------------------------------ аркуш 3 — плити
def sheet3():
    sheet(3, "Плити клітки", "1:2")
    tx(24, 274, "ПЛИТИ КЛІТКИ", 12, True)
    tx(24, 268, "вид зверху · ніс угору · DXF у fpv/cnc/ · розміри для CNC брати з DXF", 7, False, MUT)
    s = 0.5
    slots = {"horn": (70, 190), "zr10": (185, 190), "tray": (315, 190)}
    for key, pl in PLATES.items():
        b = pl["P"]; cx, cy = slots[key]
        mx, my = (b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2
        Pp = lambda x, y: (cx + (y - my) * s, cy + (x - mx) * s)
        x0, x1, y0, y1, r = pl["outline"]
        poly([Pp(y_, x_) for x_, y_ in list(C._rr(y0, y1, x0, x1, r).exterior.coords)[:-1]], 0.5, INK if pl["mat"] == "CF" else G10C, "#f2f2f2", 1)
        for k_, prm, g in pl["cut"]:
            cp = C.cut_poly(k_, prm)
            poly([Pp(*pt) for pt in list(cp.exterior.coords)[:-1]], 0.35, INK, "#ffffff", 1)
        for x, y, d, g in pl["holes"]:
            circ(*Pp(x, y), d / 2 * s + 0.15, 0.3, INK, "#ffffff", 1)
        tx(cx, cy + (x1 - x0) * s / 2 + 14, f"{PL_NAME[key]} — {pl['title']}", 9, True, INK, "c")
        tx(cx, cy + (x1 - x0) * s / 2 + 9.5, pl["note"], 6.2, False, MUT, "c")
        dim(*Pp(x1, y0), *Pp(x1, y1), f"{y1 - y0:.0f}", 5, 6.5)
        dim(*Pp(x0, y0), *Pp(x1, y0), f"{x1 - x0:.0f}", 5, 6.5)
        probs, g_ = C.check_plate(pl)
        info = [f"Маса {g_:.0f} г · {'перевірка OK' if not probs else 'ПОМИЛКИ: ' + '; '.join(probs)}"]
        groups = {}
        for x, y, d, gname in pl["holes"]: groups[(gname, d)] = groups.get((gname, d), 0) + 1
        info += [f"{n}× Ø{d} — {gname}" for (gname, d), n in groups.items()]
        cg = {}
        for _, _, g in pl["cut"]: cg[g] = cg.get(g, 0) + 1
        info += [(f"{n}× " if n > 1 else "") + f"виріз: {g}" for g, n in cg.items()]
        Yi = cy - (x1 - x0) * s / 2 - 12
        for t in info: tx(cx - 42, Yi, t, 6.3, t.startswith("Маса"), DIM if "ПОМИЛ" in t else INK); Yi -= 4.2
    Y = 88
    tx(24, Y, "Що ще треба розмітити по місцю", 9, True); Y -= 6
    for t in ("Фланець рупора (П1): отвори під фланець вашого рупора. Орієнтація горловини задає поляризацію — узгодити з ретранслятором.",
              "Кріплення SIYI ZR10 (П2): за шаблоном з комплекту підвісу. Отвір Ø30 по центру — під кабель.",
              "Короб ретранслятора (П3): тримається двома ременями 25 мм через пази; кріплення гвинтами — по місцю.",
              "Сідла J5: 2×M3 крок 28 поперек труби Ø16; на кожній плиті по 4 сідла.",
              "Отвори Ø3.2 під M3 уже з зазором. Кромки G10 зачистити — пил склопластику шкідливий, різати з відсмоктуванням."):
        tx(24, Y, "• " + t, 6.8); Y -= 5
    K.c.showPage()

# ------------------------------------------------------------------ DXF
B90 = math.tan(math.radians(90) / 4)
def dxf_plate(key, pl):
    b = pl["P"]; x0, x1, y0, y1, r = pl["outline"]
    ox, oy = y0, x0                                   # DXF: X = y (праворуч), Y = x (вперед), початок — лівий нижній кут
    Q = lambda x, y: (y - ox, x - oy)
    doc = ezdxf.new("R2000", setup=True); doc.units = units.MM
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT_OUTER", color=7); doc.layers.add("CUT_INNER", color=1)
    msp = doc.modelspace()
    def rrect(xa, xb, ya, yb, rr, layer):
        pts = [(Q(xa, ya + rr), 0), (Q(xa, yb - rr), B90), (Q(xa + rr, yb), 0), (Q(xb - rr, yb), B90),
               (Q(xb, yb - rr), 0), (Q(xb, ya + rr), B90), (Q(xb - rr, ya), 0), (Q(xa + rr, ya), B90)]
        # обхід у площині DXF має бути проти годинникової для додатних bulge — перевіряється площею нижче
        msp.add_lwpolyline([(*p, bl) for p, bl in pts], format="xyb", close=True, dxfattribs={"layer": layer})
    rrect(x0, x1, y0, y1, r, "CUT_OUTER")
    for x, y, d, g in pl["holes"]:
        msp.add_circle(Q(x, y), d / 2, dxfattribs={"layer": "CUT_INNER"})
    for k_, prm, g in pl["cut"]:
        if k_ == "rrect": rrect(prm[0], prm[1], prm[2], prm[3], prm[4], "CUT_INNER")
        elif k_ == "circle": msp.add_circle(Q(prm[0], prm[1]), prm[2], dxfattribs={"layer": "CUT_INNER"})
        elif k_ == "slot":
            cx, cy, L, W = prm; a_, r_ = (L - W) / 2, W / 2       # паз уздовж x -> у DXF уздовж Y
            pts = [(Q(cx - a_, cy + r_), 0), (Q(cx + a_, cy + r_), 1), (Q(cx + a_, cy - r_), 0), (Q(cx - a_, cy - r_), 1)]
            msp.add_lwpolyline([(*p, bl) for p, bl in pts], format="xyb", close=True, dxfattribs={"layer": "CUT_INNER"})
    path = os.path.join(CNC, f"cage_{key}.dxf"); doc.saveas(path)
    # ---- перевірка назад ----
    d2 = ezdxf.readfile(path); aud = d2.audit(); m2 = d2.modelspace()
    area = lambda e: Polygon([(v.x, v.y) for v in dxfpath.make_path(e).flattening(0.01)]).area
    ref_o = C._rr(x0, x1, y0, y1, r).area
    ref_i = sorted(C.cut_poly(k_, prm).area for k_, prm, _ in pl["cut"] if k_ != "circle")
    got_o = [area(e) for e in m2.query("LWPOLYLINE") if e.dxf.layer == "CUT_OUTER"]
    got_i = sorted(area(e) for e in m2.query("LWPOLYLINE") if e.dxf.layer == "CUT_INNER")
    n_c = len(m2.query("CIRCLE")); exp_c = len(pl["holes"]) + sum(1 for k_, _, _ in pl["cut"] if k_ == "circle")
    ok = (not aud.has_errors and len(got_o) == 1 and abs(got_o[0] - ref_o) / ref_o < 0.002 and n_c == exp_c
          and len(got_i) == len(ref_i) and all(abs(a - b_) / b_ < 0.002 for a, b_ in zip(got_i, ref_i)))
    print(f"  {os.path.basename(path)}: отворів {n_c}/{exp_c}, площа контуру {got_o[0]:.0f}/{ref_o:.0f}, "
          f"вирізи {[round(a) for a in got_i]}/{[round(a) for a in ref_i]}, аудит {'OK' if not aud.has_errors else 'ПОМИЛКИ'} -> {'OK' if ok else 'FAIL'}")
    return ok

if __name__ == "__main__":
    allok = True
    for key, pl in PLATES.items():
        probs, g = C.check_plate(pl)
        print(f"{PL_NAME[key]} {pl['title']}: {'OK' if not probs else probs}, {g:.0f} г"); allok &= not probs
    res, clear = C.mech_report(SHIFT)
    worst = min(res, key=lambda r: r[2])
    print(f"мін. механічний зазор {worst[2]:.1f} мм ({worst[0]} ↔ {worst[1]}); просвіт {clear}")
    allok &= worst[2] >= 5
    os.makedirs(CNC, exist_ok=True)
    for key, pl in PLATES.items(): allok &= dxf_plate(key, pl)
    K.new_canvas(OUT, "Клітка payload · креслення")
    sheet1(); sheet2(); sheet3(); K.c.save()
    print("PDF:", os.path.abspath(OUT))
    sys.exit(0 if allok else 1)
