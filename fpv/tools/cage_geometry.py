"""Геометрія клітки payload — єдине джерело для креслень і перевірок.

Координати: x — вперед (ніс), y — праворуч, z — вгору, z = 0 площина гвинтів. мм.
"""
import math

LAM4_900 = 299792.458 / 900 / 4          # 83.3 мм
TUBE_D, TUBE_d = 16.0, 14.0
R_T = TUBE_D / 2

# ---- силова частина ----
LEG_TOP = (115.0, 40.0, -115.0)          # вузол J1 під нижньою пластиною (x, y, z), дзеркально ±x ±y
LEG_BOT = (150.0, 290.0, -515.0)         # вузол J3 на лижі
SKID_X = (-300.0, 300.0)
Z_RAIL = -195.0
Z_XBAR = Z_RAIL - TUBE_D                 # поперечки під рейками, вісь -211

def leg_at(z, sx=1, sy=1):
    t = (z - LEG_TOP[2]) / (LEG_BOT[2] - LEG_TOP[2])
    return (sx * (LEG_TOP[0] + (LEG_BOT[0] - LEG_TOP[0]) * t), sy * (LEG_TOP[1] + (LEG_BOT[1] - LEG_TOP[1]) * t))

J2_X, J2_Y = leg_at(Z_RAIL)              # вузол ніжка–рейка
RAIL_Y = round(J2_Y - 18.0)              # рейка зсунута всередину на 18 мм від осі ніжки (хрестовий затискач)
RAIL_X = (-280.0, 280.0)
XBARS = {"X1": (50.0, (-180.0, 180.0)), "X2": (-50.0, (-180.0, 180.0))}   # приклад: крок 100 під бортові плити

BATT = dict(x0=-93.5, x1=93.5, y0=-87.0, y1=87.0, z0=-174.0, z1=-107.0)   # касета, номінальне положення
BATT_TRIM = 15.0                         # хід касети по x у пазах нижньої пластини, ±мм
BATT_KG = 5.0
PLATE_BOT = dict(x0=-125, x1=125, y0=-125, y1=125, z0=-106, z1=-104)
GROUND = LEG_BOT[2] - R_T                # низ лиж
MIN_GROUND = 30.0                        # мінімальний просвіт під навісним
Z_TOP_ZONE = Z_RAIL - R_T - 2            # верх нижніх зон: площина кріплення під рейками
Z_BOT_ZONE = GROUND + MIN_GROUND

# ---- зони встановлення: (x0, x1, y0, y1, z0, z1) ----
ZONES = {
    "A": dict(name="Носова", box=(167, 290, -272, 272, Z_BOT_ZONE, Z_TOP_ZONE), col="#b8560b",
              mount="рейки + поперечки", note="огляд вперед і вниз вільний; частково під дисками гвинтів"),
    "B": dict(name="Центральна", box=(-104, 104, -272, 272, Z_BOT_ZONE, Z_TOP_ZONE), col="#0b6fb8",
              mount="рейки + поперечки", note="найбільша; важке ставити ближче до центру"),
    "C": dict(name="Кормова", box=(-290, -167, -272, 272, Z_BOT_ZONE, Z_TOP_ZONE), col="#6b3fa0",
              mount="рейки + поперечки", note="огляд назад і вниз вільний; частково під дисками"),
    "D": dict(name="Коридори ніжок", box=(104, 167, -75, 75, Z_BOT_ZONE, Z_TOP_ZONE), col="#2e7d4f",
              mount="лише рейки", note="між ніжками; дзеркально x −167…−104; для довгих виробів"),
    "T": dict(name="Верхня", box=(-195, 195, -195, 195, -50, -6), col="#0e8a4f",
              mount="4×M4 на верхній пластині", note="коло R195 у тіні гвинтів; прямокутне — з поворотом 45°"),
    "V": dict(name="Відсік авіоніки", box=(-56, 56, -56, 56, -100, -60), col="#8c8c8c",
              mount="демпфери", note="між пластинами; зайнятий Pixhawk 6X + CM4"),
}
D_MIRROR = (-167, -104)
PROP_SHADOW_R = 575.0 - 28 * 25.4 / 2    # 219: зона під центром поза дисками гвинтів
GPS_MAST = (-230.0, 0.0)

def zone_boxes():
    """Усі прямокутні зони разом із дзеркальним коридором D."""
    out = []
    for k, z in ZONES.items():
        out.append((k, z["box"]))
        if k == "D":
            x0, x1, y0, y1, z0, z1 = z["box"]; out.append(("D", (D_MIRROR[0], D_MIRROR[1], y0, y1, z0, z1)))
    return out

def seg_pts(a, b, step=2.0):
    n = max(2, int(math.dist(a, b) / step) + 1)
    return [tuple(a[i] + (b[i] - a[i]) * k / (n - 1) for i in range(3)) for k in range(n)]

def d_box(p, B):
    dx = max(B["x0"] - p[0], 0, p[0] - B["x1"]); dy = max(B["y0"] - p[1], 0, p[1] - B["y1"]); dz = max(B["z0"] - p[2], 0, p[2] - B["z1"])
    return math.sqrt(dx * dx + dy * dy + dz * dz)

def d_seg(p, a, b):
    ab = [b[i] - a[i] for i in range(3)]; ap = [p[i] - a[i] for i in range(3)]
    L2 = sum(v * v for v in ab) or 1e-9
    t = max(0.0, min(1.0, sum(ab[i] * ap[i] for i in range(3)) / L2))
    return math.dist(p, [a[i] + ab[i] * t for i in range(3)])

def d_horn(p):
    top, bot = HORN["top"], HORN["top"] - HORN["L"]
    zc = min(max(p[2], bot), top)
    R = horn_rect(zc)
    dxy = math.hypot(max(R[0] - p[0], 0, p[0] - R[1]), max(R[2] - p[1], 0, p[1] - R[3]))
    return math.hypot(dxy, p[2] - zc)

def batt_box(shift_x=0.0):
    b = dict(BATT); b["x0"] += shift_x; b["x1"] += shift_x; return b

def segments():
    """(назва, a, b, радіус, матеріал) — трубчасті елементи клітки."""
    S = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            S.append((f"ніжка {'П' if sy > 0 else 'Л'}{'П' if sx > 0 else 'З'}",
                      (sx * LEG_TOP[0], sy * LEG_TOP[1], LEG_TOP[2]), (sx * LEG_BOT[0], sy * LEG_BOT[1], LEG_BOT[2]), R_T, "CF"))
    for sy in (-1, 1):
        S.append((f"лижа {'П' if sy > 0 else 'Л'}", (SKID_X[0], sy * LEG_BOT[1], LEG_BOT[2]), (SKID_X[1], sy * LEG_BOT[1], LEG_BOT[2]), R_T, "CF"))
        S.append((f"рейка {'П' if sy > 0 else 'Л'}", (RAIL_X[0], sy * RAIL_Y, Z_RAIL), (RAIL_X[1], sy * RAIL_Y, Z_RAIL), R_T, "G10"))
    for n, (x, (y0, y1)) in XBARS.items():
        S.append((f"поперечка {n}", (x, y0, Z_XBAR), (x, y1, Z_XBAR), R_T, "G10"))
    return S

def zone_clearance():
    """Мінімальні відстані від зон нижнього ярусу до конструкції і до землі."""
    res = {}
    segs = [sg for sg in segments() if not sg[0].startswith(("рейка", "поперечка"))]
    for k, (x0, x1, y0, y1, z0, z1) in zone_boxes():
        if k in ("T", "V"): continue
        B = dict(x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1)
        d = min(min(d_box(p, B) for p in seg_pts(a, b, 3.0)) - r for _, a, b, r, _ in segs)
        for sh in (-BATT_TRIM, BATT_TRIM):
            bb = batt_box(sh)
            if not (bb["x1"] < x0 or bb["x0"] > x1): d = min(d, bb["z0"] - z1)
        res[k] = min(res.get(k, 1e9), d)
        res["земля"] = z0 - GROUND
    return res

# ================= плити клітки: контур, отвори, вирізи =================
from shapely.geometry import Point, box as sbox
from shapely.ops import unary_union
M3, M4 = 3.2, 4.2
SADDLE_PITCH = 28.0            # сідло Ø16: 2×M3 поперек труби

def _rr(x0, x1, y0, y1, r):
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 32)

def _slot_x(cx, cy, L, W):     # паз уздовж x
    return sbox(cx - (L - W) / 2, cy, cx + (L - W) / 2, cy).buffer(W / 2, 32)

GRID = 20.0            # сітка M3 на універсальних плитах

def _grid(x0, x1, y0, y1, avoid, margin=10.0, web=6.0):
    H = []
    nx = int((x1 - x0 - 2 * margin) // GRID); ny = int((y1 - y0 - 2 * margin) // GRID)
    ox = (x0 + x1) / 2 - nx * GRID / 2; oy = (y0 + y1) / 2 - ny * GRID / 2
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = ox + i * GRID, oy + j * GRID
            if all(math.hypot(x - ax, y - ay) - (M3 + ad) / 2 >= web for ax, ay, ad in avoid):
                H.append((x, y, M3, "сітка M3 крок 20"))
    return H

def cage_plates():
    """Універсальні монтажні плити. Координати плити: x — вперед, y — праворуч, центр плити (0, 0)."""
    out = {}
    L, Wd = 130.0, 190.0
    sad = [(x, sy * RAIL_Y + dy, M3) for x in (-L / 2 + 15, L / 2 - 15) for sy in (-1, 1) for dy in (-SADDLE_PITCH / 2, SADDLE_PITCH / 2)]
    H = [(x, y, d, "сідла на рейки") for x, y, d in sad] + _grid(-L / 2, L / 2, -Wd / 2, Wd / 2, sad)
    out["center"] = dict(size=(L, Wd), t=2.0, mat="CF", outline=(-L / 2, L / 2, -Wd / 2, Wd / 2, 6.0), holes=H, cut=[],
                         title="Плита між рейками", note="CF 2 мм · 4 сідла на рейки Ø16 · будь-яке x уздовж рейок")
    L, Wd = 150.0, 150.0
    sad = [(sx * 50 + dx, y, M3) for sx in (-1, 1) for dx in (-SADDLE_PITCH / 2, SADDLE_PITCH / 2) for y in (-50.0, 50.0)]
    H = [(x, y, d, "сідла на поперечки") for x, y, d in sad] + _grid(-L / 2, L / 2, -Wd / 2, Wd / 2, sad)
    out["side"] = dict(size=(L, Wd), t=2.0, mat="G10", outline=(-L / 2, L / 2, -Wd / 2, Wd / 2, 6.0), holes=H, cut=[],
                       title="Плита бортова", note="G10 2 мм · 4 сідла на дві поперечки з кроком 100")
    return out

def cut_poly(kind, prm):
    if kind == "rrect": return _rr(*prm)
    if kind == "circle": return Point(prm[0], prm[1]).buffer(prm[2], 64)
    if kind == "slot": return _slot_x(*prm)

def check_plate(pl, min_web=6.0):
    x0, x1, y0, y1, r = pl["outline"]; outline = _rr(x0, x1, y0, y1, r)
    probs = []
    cuts = [cut_poly(k, p) for k, p, _ in pl["cut"]]
    for i, (x, y, d, g) in enumerate(pl["holes"]):
        h = Point(x, y).buffer(d / 2, 32)
        e = outline.exterior.distance(Point(x, y)) - d / 2
        if e < max(1.5 * d, 6.0): probs.append(f"{g} ({x:.0f},{y:.0f}) до краю {e:.1f}")
        for c in cuts:
            if c.distance(h) < min_web: probs.append(f"{g} ({x:.0f},{y:.0f}) до вирізу {c.distance(h):.1f}")
        for (x2, y2, d2, _) in pl["holes"][i + 1:]:
            gap = math.hypot(x - x2, y - y2) - (d + d2) / 2
            if gap < min_web: probs.append(f"перемичка ({x:.0f},{y:.0f})–({x2:.0f},{y2:.0f}) {gap:.1f}")
    for c in cuts:
        if outline.exterior.distance(c) < min_web: probs.append("виріз до краю < 6")
    mat = outline.difference(unary_union(cuts + [Point(x, y).buffer(d / 2, 32) for x, y, d, _ in pl["holes"]]))
    if mat.geom_type != "Polygon": probs.append("плита розпадається")
    rho = 1.55 if pl["mat"] == "CF" else 1.85
    return probs, mat.area * pl["t"] / 1000 * rho

# ================= труби, вузли, маса =================
LEG_CC = math.dist(LEG_TOP, LEG_BOT)
LEG_CUT = round(LEG_CC - 2 * 8)        # торець труби зупиняється за 8 мм до точки вузла
LEG_SPLAY = math.degrees(math.atan2(LEG_BOT[1] - LEG_TOP[1], LEG_TOP[2] - LEG_BOT[2]))
LEG_RAKE = math.degrees(math.atan2(LEG_BOT[0] - LEG_TOP[0], LEG_TOP[2] - LEG_BOT[2]))
LEG_TILT = math.degrees(math.acos((LEG_TOP[2] - LEG_BOT[2]) / LEG_CC))

def tubes():
    """(поз, назва, матеріал, L, к-сть)"""
    return [("Т1", "Ніжка", "CF", LEG_CUT, 4),
            ("Т2", "Лижа", "CF", SKID_X[1] - SKID_X[0], 2),
            ("Т3", "Рейка", "G10", RAIL_X[1] - RAIL_X[0], 2),
            ("Т4", "Поперечка X1", "G10", XBARS["X1"][1][1] - XBARS["X1"][1][0], 1),
            ("Т5", "Поперечка X2", "G10", XBARS["X2"][1][1] - XBARS["X2"][1][0], 1)]

def tube_kg_per_m(mat):
    return math.pi / 4 * (TUBE_D ** 2 - TUBE_d ** 2) * 1e-6 * (1550 if mat == "CF" else 1850)

JOINTS = [  # (поз, назва, к-сть, маса г, матеріал, опис)
    ("J1", "Кронштейн ніжки", 4, 12, "PA-CF", "до нижньої пластини 2×M4 крок 20; гніздо Ø16"),
    ("J2", "Хрест ніжка–рейка", 4, 10, "PA-CF", "осі зі зсувом 18 мм; ніжка під кутом до рейки"),
    ("J3", "Т-вузол ніжка–лижа", 4, 10, "PA-CF", "охоплює лижу; гніздо ніжки"),
    ("J4", "Хрест поперечка–рейка", 4, 6, "PETG", "90°, зсув осей 16 мм, поперечка під рейкою"),
    ("J5", "Сідло Ø16", 8, 3, "PETG", "2×M3 крок 28; по 4 на кожну монтажну плиту"),
    ("J7", "Заглушка лижі", 4, 2, "PETG", "")]
FASTENERS_G = 40

def cage_mass():
    """Клітка без навісного: труби, вузли J1–J4, J7, кріпіж. Монтажні плити і сідла — окремо (kit)."""
    t = sum(tube_kg_per_m(m) * L / 1000 * n for _, _, m, L, n in tubes()) * 1000
    j = sum(n * g for p_, _, n, g, _, _ in JOINTS if p_ != "J5")
    kit = sum(check_plate(pl)[1] for pl in cage_plates().values()) + sum(n * g for p_, _, n, g, _, _ in JOINTS if p_ == "J5")
    return dict(tubes=t, joints=j, fasteners=FASTENERS_G, total=t + j + FASTENERS_G, kit=kit)

# ================= бюджет навісного =================
# Апарат без навісного: планер (мотори, ESC, гвинти 28", промені Ø50, пластини 250×250), авіоніка
# (Pixhawk 6X + CM4, GPS, PM, демпфери), силова проводка, клітка. Виведено з повного AUW 13.84 кг
# вилученням батареї (5.0), виробів (3.351), їхніх плит і сідел (0.277) і старої клітки (0.848).
BASE_EXCL_CAGE = 13.84 - 5.0 - 3.351 - 0.277 - 0.848
def base_kg():
    return BASE_EXCL_CAGE + cage_mass()["total"] / 1000

MAX_T_MOTOR = 8.5       # кг, MN6012 KV170 + 28" складаний, 12S, рівень моря
def perf(auw, pay_w=0.0, D=28, n=4, fm=0.51, avi=35.0, E=1732.0, alt=1500):
    rho = 1.225 * (1 - 2.25577e-5 * alt) ** 4.25588
    T = auw / n * 9.81; A = math.pi * (D * 0.0254 / 2) ** 2
    P = (T ** 1.5 / math.sqrt(2 * rho * A)) / fm * n + avi + pay_w
    return P, E * 0.88 / P * 60 - 3, (MAX_T_MOTOR * n * rho / 1.225) / auw

def payload_max(tw_min=2.0):
    rho = 1.225 * (1 - 2.25577e-5 * 1500) ** 4.25588
    return MAX_T_MOTOR * 4 * rho / 1.225 / tw_min - base_kg() - BATT_KG

CG_TARGET_MM = 10.0     # цільове зміщення ЦМ апарата
def cg_limits(auw):
    """Допустимі сумарні моменти навісного (кг·мм) відносно центру апарата."""
    trim = BATT_KG * BATT_TRIM
    return dict(x=CG_TARGET_MM * auw + trim, y=CG_TARGET_MM * auw, trim=trim)
