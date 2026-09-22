"""Клітка payload і зони встановлення -> fpv/cage-drawings.pdf (5 аркушів A3),
універсальні монтажні плити -> fpv/cnc/cage_plate_*.dxf

Геометрія — cage_geometry.py; примітиви і штамп — make_sketch.py.
Запуск: python3 fpv/tools/make_cage.py
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cage_geometry as C
import plate_geometry as G
import make_sketch as K
from make_sketch import ln, rect, poly, circ, tx, dim, balloon, arrowhead, INK, DIM, MUT, ACC, PWR, SLC
import ezdxf
from ezdxf import units
from ezdxf import path as dxfpath
from shapely.geometry import Polygon

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "cage-drawings.pdf")
CNC = os.path.join(HERE, "..", "cnc")
TOTAL = 5
G10C = "#2e7d4f"
PLATES = C.cage_plates()
PL_NAME = {"center": "П1", "side": "П2"}
mz = K.mz

def sheet(n, title, scale): K.sheet(n, TOTAL, title, scale)

def draw_structure(proj, s, battery=True, plate=True):
    """Конструкція клітки у заданій проекції proj(x, y, z) -> (px, py)."""
    for n, a, b, r, mat in C.segments():
        col = INK if mat == "CF" else G10C
        pa, pb = proj(*a), proj(*b)
        if math.dist(pa, pb) < 0.5: circ(*pa, r * s + 0.15, 0.35, col, col, 1)
        else: ln(*pa, *pb, 2 * r * s, col); ln(*pa, *pb, 0.12, "#ffffff")

def box_proj(proj, b):
    x0, x1, y0, y1, z0, z1 = b
    pts = [proj(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)

def draw_zone(proj, k, b, tag=True, lw=0.35, alpha=0.07, tagpos=None):
    col = C.ZONES[k]["col"]; X, Y, Wd, Ht = box_proj(proj, b)
    rect(X, Y, Wd, Ht, lw, col, col, alpha, dash=(2, 1.2))
    if tag:
        tx_, ty_ = tagpos if tagpos else (X + Wd / 2, Y + Ht / 2)
        K.zone_tag(tx_, ty_, k, col)

def views():
    s = 0.2
    P = lambda x, y, z=0: (95 + y * s, 195 + x * s)            # план: ніс угору
    S = lambda x, y, z: (235 + x * s, 272 + z * s)             # збоку: ніс праворуч
    F = lambda x, y, z: (235 - y * s, 158 + z * s)             # спереду: правий борт ліворуч
    return s, P, S, F

# ================================================================== 1. зони
def sheet_zones():
    sheet(1, "Зони встановлення навісного", "1:5")
    s, P, S, F = views()
    tx(24, 274, "ЗОНИ ВСТАНОВЛЕННЯ НАВІСНОГО", 12, True)
    tx(24, 268, "об'єми, вільні від конструкції; навісне в межах зони не торкається ніжок, лиж, батареї і землі", 7, False, MUT)
    # --- план ---
    tx(24, 258, "План", 9, True)
    poly([P(y, x) for x, y in list(G.outline_poly().exterior.coords)[:-1]], 0.25, MUT, dash=(2, 1.5))
    circ(*P(0, 0), C.PROP_SHADOW_R * s, 0.25, MUT, dash=(3, 2))
    for k, b in C.zone_boxes():
        if k in ("V",): continue
        if k == "T":
            circ(*P(0, 0), 195 * s, 0.4, C.ZONES["T"]["col"], C.ZONES["T"]["col"], 0.05, dash=(2, 1.2)); continue
        X, Y, Wd, Ht = box_proj(P, b)
        draw_zone(P, k, b, tagpos=(X + Wd / 2, Y + Ht - 4.5))
    draw_structure(P, s)
    K.zone_tag(*P(0, -205), "T", C.ZONES["T"]["col"])
    tx(24, 250, "НІС ↑", 7, True)
    tx(*P(C.PROP_SHADOW_R * 0.7, C.PROP_SHADOW_R * 0.72), "тінь R219", 5.8, False, MUT)
    zA, zB, zC, zD = (C.ZONES[k]["box"] for k in "ABCD")
    dim(*P(zC[0], -290), *P(zA[1], -290), f"{zA[1] - zC[0]:.0f}", 5, 6.3)
    dim(*P(-300, zB[2]), *P(-300, zB[3]), f"{zB[3] - zB[2]:.0f}", -4, 6.3)
    # --- вид збоку ---
    tx(176, 278, "Вид збоку (з правого борту)", 9, True)
    ln(*S(-300, 0, 0), *S(300, 0, 0), 0.6, MUT)
    ln(*S(-125, 0, -105), *S(125, 0, -105), 0.8, MUT)
    ln(*S(-125, 0, -55), *S(125, 0, -55), 0.8, MUT)
    bb = C.batt_box(0); x0, y0 = S(bb["x0"], 0, bb["z0"]); rect(x0, y0, (bb["x1"] - bb["x0"]) * s, (bb["z1"] - bb["z0"]) * s, 0.25, PWR, PWR, 0.05, dash=(2, 1.5))
    for k, b in C.zone_boxes():
        if k == "V": continue
        draw_zone(S, k, b)
    draw_structure(S, s)
    ln(*S(-310, 0, C.GROUND), *S(310, 0, C.GROUND), 0.2, MUT)
    dim(*S(300, 0, C.Z_BOT_ZONE), *S(300, 0, C.Z_TOP_ZONE), f"{C.Z_TOP_ZONE - C.Z_BOT_ZONE:.0f}", 0, 6.3)
    dim(*S(-300, 0, C.GROUND), *S(-300, 0, C.Z_BOT_ZONE), f"{C.MIN_GROUND:.0f}", 5, 6)
    t = C.ZONES["T"]["box"]
    dim(*S(210, 0, t[4]), *S(210, 0, t[5]), f"{t[5] - t[4]:.0f}", 0, 6)
    tx(*S(-300, 0, 3), "площина гвинтів z 0", 5.8, False, MUT)
    # --- вид спереду ---
    tx(176, 163, "Вид спереду (з боку носа; правий борт ліворуч)", 9, True)
    ln(*F(0, -125, -105), *F(0, 125, -105), 0.8, MUT); ln(*F(0, -125, -55), *F(0, 125, -55), 0.8, MUT)
    for k, b in C.zone_boxes():
        if k in ("V", "A", "C"): continue
        X, Y, Wd, Ht = box_proj(F, b)
        draw_zone(F, k, b, tag=(k != "B"))
        if k == "B":
            for i_, kk in enumerate("ABC"): K.zone_tag(X + 6 + i_ * 6.5, Y + Ht - 5, kk, C.ZONES[kk]["col"])
    draw_structure(F, s)
    ln(*F(0, 310, C.GROUND), *F(0, -310, C.GROUND), 0.2, MUT)
    dim(*F(0, zB[3], C.Z_BOT_ZONE - 12), *F(0, zB[2], C.Z_BOT_ZONE - 12), f"{zB[3] - zB[2]:.0f}", 0, 6)
    dim(*F(0, zD[3], C.Z_BOT_ZONE + 20), *F(0, zD[2], C.Z_BOT_ZONE + 20), f"D {zD[3] - zD[2]:.0f}", 0, 6)
    # --- таблиця зон ---
    X = 305; Y = 272
    tx(X, Y, "Зони", 10, True); Y -= 6.5
    for k, z in C.ZONES.items():
        x0, x1, y0, y1, z0, z1 = z["box"]
        K.zone_tag(X + 2.6, Y + 1.1, k, z["col"])
        tx(X + 7, Y, f"{z['name']} — {x1 - x0:.0f}×{y1 - y0:.0f}×{z1 - z0:.0f}", 7.2, True); Y -= 4.3
        if k == "T": tx(X + 7, Y, "коло R195 · від пластини до −6 під гвинтами", 6.2, False, MUT)
        else: tx(X + 7, Y, f"x {mz(x0)}…{mz(x1)}, y {mz(y0)}…{mz(y1)}, z {mz(z0)}…{mz(z1)}", 6.2, False, MUT)
        Y -= 3.9; tx(X + 7, Y, "кріплення: " + z["mount"], 6.2); Y -= 3.9
        tx(X + 7, Y, z["note"], 6.2, False, MUT); Y -= 5.6
    Y -= 1
    tx(X, Y, "Правила", 9, True); Y -= 5.5
    rules = [f"Зазор зон до конструкції ≥ 10 мм, просвіт {C.MIN_GROUND:.0f} мм.",
             "Верх зон A–D — під рейками; кріплення бере 2–16 мм.",
             "Поперечки між x 104…167 не ставити — там ніжки.",
             f"Під дисками гвинтів (за колом R{C.PROP_SHADOW_R:.0f}) навісне",
             "перекриває струмінь — ставити туди лише плоске.",
             "Антени < 1 ГГц: ≥ λ/4 (83 мм на 900 МГц) від",
             "карбону й металу; кріплення біля них — G10/PETG.",
             "Передавачі — далі від щогли GPS (x −230)."]
    for t_ in rules: tx(X, Y, t_, 6.4); Y -= 4.2
    # --- легенда під планом ---
    Y = 124
    tx(24, Y, "Інтерфейс кріплення", 9, True); Y -= 5.5
    for t_ in (f"Рейки G10 Ø16 · y ±{C.RAIL_Y:.0f} · z {mz(C.Z_RAIL)} · x {mz(C.RAIL_X[0])}…{mz(C.RAIL_X[1])}",
               "Сідла J5: 2×M3 крок 28, будь-яке місце на трубі",
               f"Поперечки G10 Ø16 під рейками (z {mz(C.Z_XBAR)}) — за потреби,",
               "будь-яке x поза коридорами D, довжина до ±272",
               "Плити П1 (між рейками) і П2 (бортова) — сітка M3 крок 20",
               "Зона T: 4×M4 на верхній пластині (±90, ±20)"):
        tx(24, Y, t_, 6.5); Y -= 4.2
    Y -= 3
    for col, t_ in ((INK, "карбон"), (G10C, "склопластик G10"), (MUT, "рама, тінь гвинтів"), (PWR, "касета батареї")):
        rect(24, Y - 0.8, 5, 3, 0.3, col, col, 0.3); tx(31, Y, t_, 6.5); Y -= 4.4
    K.c.showPage()

# ================================================================== 2. бюджет
def sheet_budget():
    sheet(2, "Бюджет навісного", "б/м")
    tx(24, 274, "БЮДЖЕТ НАВІСНОГО — ДЛЯ ВЛАСНОГО РОЗРАХУНКУ", 12, True)
    base = C.base_kg(); auw0 = base + C.BATT_KG; pmax = C.payload_max()
    tx(24, 266, f"Апарат без навісного {base:.2f} кг + батарея {C.BATT_KG:.1f} кг = {auw0:.2f} кг. Модель: висіння на 1500 м, штиль, "
                f"батарея 12S 1732 Вт·год, використання 88 %, мінус 3 хв на набір висоти.", 7, False, MUT)
    powers = (0, 50, 100, 150, 200)
    X = 24; Y = 252
    tx(X, Y, "Час висіння, хв — за масою і споживанням навісного", 10, True); Y -= 8
    cols = [X, X + 30, X + 52] + [X + 80 + i * 24 for i in range(len(powers))]
    tx(cols[0], Y, "Маса, кг", 7, True, MUT); tx(cols[1], Y, "AUW", 7, True, MUT); tx(cols[2], Y, "T/W", 7, True, MUT)
    for i, pw in enumerate(powers): tx(cols[3 + i], Y, f"{pw} Вт", 7, True, MUT)
    Y -= 2; ln(X, Y, cols[-1] + 18, Y, 0.25, MUT); Y -= 5.5
    m = 0.0
    while m <= pmax + 0.51:
        auw = auw0 + m; _, _, tw = C.perf(auw)
        bad = tw < 2.0
        col = DIM if bad else INK
        tx(cols[0], Y, f"{m:.1f}", 7.5, True, col); tx(cols[1], Y, f"{auw:.1f}", 7.5, False, col); tx(cols[2], Y, f"{tw:.2f}", 7.5, False, col)
        for i, pw in enumerate(powers):
            tx(cols[3 + i], Y, f"{C.perf(auw, pw)[1]:.0f}", 7.5, False, col)
        Y -= 5.2; m += 0.5
    tx(X, Y - 1, f"Червоне — T/W нижче 2.0: запасу тяги на 1500 м не вистачає для вітру і маневру. Межа — {pmax:.2f} кг навісного.", 6.8, False, DIM)
    Y -= 7
    tx(X, Y, "Маса навісного — разом з кронштейнами, плитами П1/П2, сідлами, фідерами і DC-DC.", 6.8); Y -= 4.4
    tx(X, Y, "Споживання — середнє з батареї, з урахуванням ККД перетворювачів (~90 %).", 6.8); Y -= 4.4
    ref = 3.63
    tx(X, Y, f"Орієнтир: попередній набір (Starlink, ZR10, рупор, Ягі, ретранслятор) — {ref:.1f} кг, ~96 Вт → "
              f"{C.perf(auw0 + ref, 96)[1]:.0f} хв, T/W {C.perf(auw0 + ref)[2]:.2f}.", 6.8, False, MUT)
    # --- ЦМ ---
    X = 262; Y = 252
    lim = C.cg_limits(auw0 + 3.0)
    tx(X, Y, "Центр мас", 10, True); Y -= 7
    for t_ in ("Для кожного виробу i: маса mᵢ (кг) і координати центру",
               "xᵢ (вперед +), yᵢ (праворуч +) у мм від центру апарата.",
               "", "Mx = Σ mᵢ·xᵢ,   My = Σ mᵢ·yᵢ   (кг·мм)", "",
               f"Касета батареї ходить у пазах ±{C.BATT_TRIM:.0f} мм і компенсує",
               f"по x до ±{lim['trim']:.0f} кг·мм. Зсув касети: Δx = −Mx / {C.BATT_KG:.0f} кг.",
               "По y компенсації немає — розкладати навісне симетрично.", "",
               f"Ціль — ЦМ апарата ≤ {C.CG_TARGET_MM:.0f} мм від центру. При AUW ≈ {auw0 + 3:.0f} кг:",
               f"   |Mx| ≤ {lim['x']:.0f} кг·мм (з урахуванням касети)",
               f"   |My| ≤ {lim['y']:.0f} кг·мм"):
        tx(X, Y, t_, 7.2, t_.startswith(("Mx", "   |")), DIM if t_.startswith("   |") else INK); Y -= 4.6
    Y -= 4
    tx(X, Y, "Приклад", 9, True); Y -= 6
    for t_ in ("Камера 0.5 кг у зоні A (x +220) і антена 0.6 кг у зоні C",
               "(x −230): Mx = 0.5·220 − 0.6·230 = −28 кг·мм.",
               "Касета: Δx = +28 / 5 = +5.6 мм вперед. У межах ±15.",
               "Starlink 1.3 кг у зоні T по центру: момент 0."):
        tx(X, Y, t_, 7); Y -= 4.4
    Y -= 5
    tx(X, Y, "Висота центру мас", 9, True); Y -= 6
    for t_ in ("Навісне під рамою опускає ЦМ; маятникова мода",
               "f ≈ 0.5/π·√(g/h), h — глибина ЦМ під площиною гвинтів.",
               "При h > 80 мм вона падає нижче ~1.8 Гц і лягає",
               "в контур утримання позиції — знижувати PSC_POSXY_P",
               "і PSC_VELXY_P за логом."):
        tx(X, Y, t_, 7); Y -= 4.4
    K.c.showPage()

# ================================================================== 3. складальне
def sheet_assembly():
    sheet(3, "Клітка · складальне", "1:5")
    s, P, S, F = views()
    tx(24, 274, "КЛІТКА — СКЛАДАЛЬНЕ КРЕСЛЕННЯ", 12, True)
    tx(24, 268, "чорне — карбон, зелене — склопластик G10 · поперечки і плити показані як приклад розстановки", 7, False, MUT)
    tx(24, 258, "План", 9, True)
    poly([P(y, x) for x, y in list(G.outline_poly().exterior.coords)[:-1]], 0.25, MUT, dash=(2, 1.5))
    for (cx, cy), key in (((150, 0), "center"), ((0, 150), "side"), ((0, -150), "side")):
        L, Wd = PLATES[key]["size"]; X, Y, W_, H_ = box_proj(P, (cx - L / 2, cx + L / 2, cy - Wd / 2, cy + Wd / 2, 0, 0))
        rect(X, Y, W_, H_, 0.3, INK if PLATES[key]["mat"] == "CF" else G10C, "#dddddd", 0.5)
    draw_structure(P, s)
    for sx in (-1, 1):
        for sy in (-1, 1): circ(*P(sx * C.LEG_TOP[0], sy * C.LEG_TOP[1]), 1.0, 0.3, INK, "#ffffff", 1)
    tx(24, 250, "НІС ↑", 7, True)
    dim(*P(-300, -C.LEG_BOT[1]), *P(-300, C.LEG_BOT[1]), f"колія {2 * C.LEG_BOT[1]:.0f}", -5, 6.5)
    dim(*P(C.SKID_X[0], -C.LEG_BOT[1]), *P(C.SKID_X[1], -C.LEG_BOT[1]), f"{C.SKID_X[1] - C.SKID_X[0]:.0f}", 5, 6.5)
    dim(*P(C.RAIL_X[0], -C.RAIL_Y), *P(C.RAIL_X[0], C.RAIL_Y), f"{2 * C.RAIL_Y:.0f}", -1.5, 6)
    B = [("Т1", P(-137, -165), (30, 238)), ("Т2", P(-250, -290), (30, 150)), ("Т3", P(250, -C.RAIL_Y), (60, 262)),
         ("Т4", P(C.XBARS["X1"][0], -220), (162, 225)), ("Т5", P(C.XBARS["X2"][0], -220), (162, 186)),
         ("П1", P(170, 40), (162, 250)), ("П2", P(20, 190), (162, 205))]
    for n, (ax, ay), (bx, by) in B: balloon(n, ax, ay, bx, by)
    tx(176, 278, "Вид збоку (з правого борту)", 9, True)
    ln(*S(-125, 0, -105), *S(125, 0, -105), 0.8, MUT)
    draw_structure(S, s)
    ln(*S(-310, 0, C.GROUND), *S(310, 0, C.GROUND), 0.2, MUT)
    dim(*S(305, 0, C.GROUND), *S(305, 0, -105), f"{-105 - C.GROUND:.0f}", 0, 6.5)
    B = [("J1", S(115, 0, -115), (297, 272)), ("J2", S(C.J2_X, 0, C.Z_RAIL), (292, 258)), ("J3", S(150, 0, C.LEG_BOT[2]), (292, 190)),
         ("J4", S(C.XBARS["X1"][0], 0, C.Z_XBAR), (250, 268)), ("J7", S(C.SKID_X[1], 0, C.LEG_BOT[2]), (292, 175))]
    for n, (ax, ay), (bx, by) in B: balloon(n, ax, ay, bx, by)
    tx(176, 163, "Вид спереду (з боку носа; правий борт ліворуч)", 9, True)
    ln(*F(0, -125, -105), *F(0, 125, -105), 0.8, MUT)
    draw_structure(F, s)
    for (cy, zz, key) in ((0, C.Z_RAIL - C.R_T - 2, "center"), (150, C.Z_XBAR - C.R_T - 2, "side"), (-150, C.Z_XBAR - C.R_T - 2, "side")):
        Wd = PLATES[key]["size"][1]; X, Y, W_, H_ = box_proj(F, (0, 0, cy - Wd / 2, cy + Wd / 2, zz, zz + 2))
        rect(X, Y, W_, max(H_, 0.5), 0.3, INK if PLATES[key]["mat"] == "CF" else G10C, INK, 0.7)
    ln(*F(0, 310, C.GROUND), *F(0, -310, C.GROUND), 0.2, MUT)
    dim(*F(0, -C.J2_Y, C.Z_RAIL - 60), *F(0, -C.RAIL_Y, C.Z_RAIL - 60), "18", -3, 5.5)
    tx(*F(0, C.LEG_BOT[1] - 30, C.GROUND + 60), f"{C.LEG_SPLAY:.1f}°", 6.5, True, DIM, "c")
    balloon("J5", *F(0, 60, C.Z_RAIL - 8), 292, 120)
    X = 305; Y = 272
    tx(X, Y, "Специфікація клітки", 10, True); Y -= 6.5
    tx(X, Y, "Поз.", 6.3, True, MUT); tx(X + 9, Y, "Найменування", 6.3, True, MUT); tx(406, Y, "К-сть", 6.3, True, MUT, "r"); Y -= 1.6
    ln(X, Y, 408, Y, 0.2, MUT); Y -= 4
    rows = [(p, f"{nm} {m} Ø16×14, L {L:.0f}", n) for p, nm, m, L, n in C.tubes()]
    rows += [(PL_NAME[k], f"{pl['title']} {pl['mat']} {pl['t']:.0f} мм", "за потр.") for k, pl in PLATES.items()]
    rows += [(p, f"{nm} · {mat}", (n if p != "J5" else "4 на плиту")) for p, nm, n, g, mat, _ in C.JOINTS]
    for p, nm, n in rows:
        tx(X + 1, Y, p, 6.6, True); tx(X + 9, Y, nm, 6.6); tx(406, Y, str(n), 6.6, False, INK, "r"); Y -= 4.3
    Y = 124; m = C.cage_mass()
    tx(24, Y, "Примітки", 9, True); Y -= 6
    for t_ in ("Рейки й поперечки — G10, намотана трубка: радіопрозорі біля антен.",
               "Ніжки й лижі — карбон, несуть посадку.",
               "Поперечки Т4/Т5 показано з кроком 100 під плити П2 —",
               "ставити де потрібно, крім коридорів ніжок (x ±104…167).",
               f"Маса клітки {m['total']:.0f} г: труби {m['tubes']:.0f}, вузли {m['joints']:.0f}, кріпіж {m['fasteners']:.0f}.",
               f"Монтажний комплект (дві П2 + одна П1 + сідла) — {m['kit']:.0f} г, рахувати в навісне."):
        tx(24, Y, t_, 6.6); Y -= 4.4
    K.c.showPage()

# ================================================================== 4. труби і вузли
def sheet_parts():
    sheet(4, "Труби · вузли", "б/м")
    tx(24, 274, "ТРУБИ І ВУЗЛИ", 12, True)
    X = 24; Y = 262
    tx(X, Y, "Розкрій труб Ø16×14", 10, True); Y -= 7
    for t, dx in (("Поз.", 0), ("Найменування", 12), ("Матеріал", 62), ("L різу", 90), ("К-сть", 110), ("Маса", 126)):
        tx(X + dx, Y, t, 6.8, True, MUT)
    Y -= 2; ln(X, Y, X + 140, Y, 0.2, MUT); Y -= 5
    tot = 0
    for p, nm, mat, L, n in C.tubes():
        g = C.tube_kg_per_m(mat) * L / 1000 * n * 1000; tot += g
        for t, dx in ((p, 0), (nm, 12), ("карбон" if mat == "CF" else "склопластик G10", 62), (f"{L:.0f}", 90), (str(n), 110), (f"{g:.0f} г", 126)):
            tx(X + dx, Y, t, 7.2, dx == 0, INK if mat == "CF" else G10C)
        Y -= 5.4
    tx(X + 90, Y, "разом", 7, True, MUT); tx(X + 126, Y, f"{tot:.0f} г", 7.2, True); Y -= 6
    tx(X, Y, f"Ніжка: між точками вузлів {C.LEG_CC:.1f} мм; торець зупиняється за 8 мм до точки вузла → різ {C.LEG_CUT}.", 6.8); Y -= 4.5
    tx(X, Y, "Рейки, лижі й поперечки проходять крізь вузли. Поперечки Т4/Т5 — довжина під ваше навісне (тут до ±180).", 6.8); Y -= 4.5
    tx(X, Y, "Склопластик — трубка FR4/G10 намотана, не пултрузійна: пултрузія розшаровується в хомутах.", 6.8, False, DIM)
    Y -= 12
    tx(X, Y, "Вузли (друк)", 10, True); Y -= 7
    for t, dx in (("Поз.", 0), ("Назва", 12), ("Матеріал", 62), ("К-сть", 82), ("Маса", 96), ("Опис", 112)):
        tx(X + dx, Y, t, 6.8, True, MUT)
    Y -= 2; ln(X, Y, X + 230, Y, 0.2, MUT); Y -= 5
    for p, nm, n, g, mat, desc in C.JOINTS:
        for t, dx in ((p, 0), (nm, 12), (mat, 62), (str(n) if p != "J5" else "4/плита", 82), (f"{g} г/шт", 96), (desc, 112)):
            tx(X + dx, Y, t, 7, dx == 0)
        Y -= 5.2
    tx(X, Y - 1, "PA-CF — лише вузли ніжок (J1–J3). Вузли, що можуть опинитись біля антен (J4, J5, J7), — PETG без вуглецю.", 6.8, False, DIM)
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
    tx(262, gy - dz_ * sc / 2 - 20, f"Від вертикалі {C.LEG_TILT:.1f}°. Гнізда J1 і J3 друкувати під цей складений кут.", 6.6)
    dx0, dy0 = 272, 118
    tx(262, 138, "Зсув осей у хрестах", 10, True)
    for i, (lbl, off) in enumerate((("J2 ніжка–рейка", 18.0), ("J4 поперечка–рейка", 16.0))):
        cx = dx0 + i * 62
        circ(cx, dy0, 8 * 0.9, 0.4, G10C, "#ffffff", 1); circ(cx + off * 0.9, dy0, 8 * 0.9, 0.4, INK if i == 0 else G10C, "#ffffff", 1)
        dim(cx, dy0 - 10, cx + off * 0.9, dy0 - 10, f"{off:.0f}", -3, 6)
        tx(cx + off * 0.45, dy0 + 11, lbl, 6.6, True, INK, "c")
    tx(262, 96, "Осі не перетинаються — труби проходять одна повз одну,", 6.6)
    tx(262, 91.5, "хомут тримає обидві.", 6.6)
    K.c.showPage()

# ================================================================== 5. плити
def sheet_plates():
    sheet(5, "Монтажні плити", "1:2")
    tx(24, 274, "УНІВЕРСАЛЬНІ МОНТАЖНІ ПЛИТИ", 12, True)
    tx(24, 268, "вид зверху · ніс угору · сітка M3 крок 20 під будь-яке навісне · DXF у fpv/cnc/", 7, False, MUT)
    s = 0.5
    slots = {"center": (110, 185), "side": (285, 185)}
    for key, pl in PLATES.items():
        cx, cy = slots[key]; x0, x1, y0, y1, r = pl["outline"]
        Pp = lambda x, y: (cx + y * s, cy + x * s)
        poly([Pp(x_, y_) for y_, x_ in list(C._rr(y0, y1, x0, x1, r).exterior.coords)[:-1]], 0.5, INK if pl["mat"] == "CF" else G10C, "#f2f2f2", 1)
        for x, y, d, g in pl["holes"]:
            circ(*Pp(x, y), d / 2 * s + 0.15, 0.3, INK if g.startswith("сідла") else MUT, "#ffffff", 1)
        tx(cx, cy + (x1 - x0) * s / 2 + 14, f"{PL_NAME[key]} — {pl['title']}", 9, True, INK, "c")
        tx(cx, cy + (x1 - x0) * s / 2 + 9.5, pl["note"], 6.2, False, MUT, "c")
        dim(*Pp(x1, y0), *Pp(x1, y1), f"{y1 - y0:.0f}", 5, 6.5)
        dim(*Pp(x0, y0), *Pp(x1, y0), f"{x1 - x0:.0f}", 5, 6.5)
        probs, g_ = C.check_plate(pl)
        groups = {}
        for x, y, d, gname in pl["holes"]: groups[(gname, d)] = groups.get((gname, d), 0) + 1
        Yi = cy - (x1 - x0) * s / 2 - 12
        for t in [f"Маса {g_:.0f} г · {'перевірка OK' if not probs else 'ПОМИЛКИ: ' + '; '.join(probs)}"] + \
                 [f"{n}× Ø{d} — {gname}" for (gname, d), n in groups.items()]:
            tx(cx - 40, Yi, t, 6.4, t.startswith("Маса"), DIM if "ПОМИЛ" in t else INK); Yi -= 4.3
    Y = 92
    tx(24, Y, "Як користуватись", 9, True); Y -= 6
    for t in ("П1 лягає під рейки (сідла зверху на рейках) у будь-якому місці по x. Під кілька виробів — кілька плит.",
              "П2 кріпиться під дві поперечки з кроком 100 мм. Поперечки — будь-яке x поза коридорами ніжок (x ±104…167).",
              "Вироби кріпляться до сітки M3 крок 20 напряму або через перехідник; отвори під конкретний виріб — по місцю.",
              "Біля антен нижче 1 ГГц використовувати П2 (G10): карбонова П1 поруч з антеною її розстроює.",
              "Отвори Ø3.2 під M3 уже з зазором. G10 різати з відсмоктуванням пилу."):
        tx(24, Y, "• " + t, 6.8); Y -= 5
    K.c.showPage()

# ================================================================== DXF
B90 = math.tan(math.radians(90) / 4)
def dxf_plate(key, pl):
    x0, x1, y0, y1, r = pl["outline"]
    ox, oy = y0, x0                                   # DXF: X = y (праворуч), Y = x (вперед), початок — лівий нижній кут
    Q = lambda x, y: (y - ox, x - oy)
    doc = ezdxf.new("R2000", setup=True); doc.units = units.MM
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT_OUTER", color=7); doc.layers.add("CUT_INNER", color=1)
    msp = doc.modelspace()
    pts = [(Q(x0, y0 + r), 0), (Q(x0, y1 - r), B90), (Q(x0 + r, y1), 0), (Q(x1 - r, y1), B90),
           (Q(x1, y1 - r), 0), (Q(x1, y0 + r), B90), (Q(x1 - r, y0), 0), (Q(x0 + r, y0), B90)]
    msp.add_lwpolyline([(*p, bl) for p, bl in pts], format="xyb", close=True, dxfattribs={"layer": "CUT_OUTER"})
    for x, y, d, g in pl["holes"]:
        msp.add_circle(Q(x, y), d / 2, dxfattribs={"layer": "CUT_INNER"})
    path = os.path.join(CNC, f"cage_plate_{key}.dxf"); doc.saveas(path)
    d2 = ezdxf.readfile(path); aud = d2.audit(); m2 = d2.modelspace()
    area = lambda e: Polygon([(v.x, v.y) for v in dxfpath.make_path(e).flattening(0.01)]).area
    ref = C._rr(x0, x1, y0, y1, r).area
    got = [area(e) for e in m2.query("LWPOLYLINE")]
    n_c = len(m2.query("CIRCLE"))
    ok = not aud.has_errors and len(got) == 1 and abs(got[0] - ref) / ref < 0.002 and n_c == len(pl["holes"])
    print(f"  {os.path.basename(path)}: отворів {n_c}/{len(pl['holes'])}, площа контуру {got[0]:.0f}/{ref:.0f}, "
          f"аудит {'OK' if not aud.has_errors else 'ПОМИЛКИ'} -> {'OK' if ok else 'FAIL'}")
    return ok

if __name__ == "__main__":
    allok = True
    zc = C.zone_clearance()
    print("зони до конструкції (мм):", {k: round(v, 1) for k, v in zc.items()})
    allok &= all(v >= 10 for k, v in zc.items() if k != "земля") and zc["земля"] >= C.MIN_GROUND
    for key, pl in PLATES.items():
        probs, g = C.check_plate(pl)
        print(f"{PL_NAME[key]} {pl['title']}: {'OK' if not probs else probs}, {g:.0f} г"); allok &= not probs
    os.makedirs(CNC, exist_ok=True)
    for key, pl in PLATES.items(): allok &= dxf_plate(key, pl)
    for old in ("cage_horn.dxf", "cage_zr10.dxf", "cage_tray.dxf"):
        op = os.path.join(CNC, old)
        if os.path.exists(op): os.remove(op); print("  видалено застарілий", old)
    K.new_canvas(OUT, "Клітка payload · зони встановлення")
    sheet_zones(); sheet_budget(); sheet_assembly(); sheet_parts(); sheet_plates(); K.c.save()
    print(f"апарат без навісного {C.base_kg():.2f} кг, бюджет навісного {C.payload_max():.2f} кг")
    print("PDF:", os.path.abspath(OUT))
    sys.exit(0 if allok else 1)
