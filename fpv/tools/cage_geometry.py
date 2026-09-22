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
XBARS = {"X1": (30.0, (-155.0, 180.0)), "X2": (-40.0, (-90.0, 180.0))}

# ---- payload ----
YAGI = dict(x=30.0, y=-130.0, top=Z_XBAR - R_T - 4, elems=((175, 10), (167, 70), (155, 135), (150, 200), (145, 260)), boom=266.0, m=0.40)
HORN = dict(x=-185.0, y=0.0, top=Z_RAIL + R_T + 3, L=283.0, ap=226.0, thr=70.0, m=0.60)
ZR10 = dict(x=200.0, y=0.0, w=128.0, h=152.0, top=Z_RAIL - R_T - 7, m=0.53)
REP = dict(x=20.0, y=110.0, lx=150.0, ly=110.0, h=60.0, top=Z_XBAR - R_T - 3, m=0.50)
BATT = dict(x0=-93.5, x1=93.5, y0=-87.0, y1=87.0, z0=-174.0, z1=-107.0)   # до зсуву
PLATE_BOT = dict(x0=-125, x1=125, y0=-125, y1=125, z0=-106, z1=-104)
# плити на рейках
P_HORN = dict(x0=-245.0, x1=-140.0, y0=-95.0, y1=95.0, z0=Z_RAIL + R_T, z1=Z_RAIL + R_T + 3, t=3.0, mat="CF")
P_ZR10 = dict(x0=140.0, x1=270.0, y0=-95.0, y1=95.0, z0=Z_RAIL - R_T - 2, z1=Z_RAIL - R_T, t=2.0, mat="CF")
T_REP = dict(x0=-70.0, x1=95.0, y0=40.0, y1=180.0, z0=REP["top"] - 2, z1=REP["top"], t=2.0, mat="G10")

def yagi_elems():
    return [(YAGI["top"] - dz, L) for L, dz in YAGI["elems"]]

def horn_rect(z):
    top, L = HORN["top"], HORN["L"]
    k = min(max((top - z) / L, 0.0), 1.0)
    h = (HORN["thr"] + (HORN["ap"] - HORN["thr"]) * k) / 2
    return (HORN["x"] - h, HORN["x"] + h, HORN["y"] - h, HORN["y"] + h)

# ---- примітиви відстаней (вибірка точок, крок 2 мм) ----
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

def batt_box(shift_x):
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

def payload_mass_moment(shift_x=0.0):
    items = [(ZR10["m"], ZR10["x"], ZR10["y"]), (REP["m"], REP["x"], REP["y"]),
             (HORN["m"], HORN["x"], HORN["y"]), (YAGI["m"], YAGI["x"], YAGI["y"])]
    return sum(m * x for m, x, _ in items), sum(m * y for m, _, y in items)

def battery_trim(auw=13.48, batt_m=5.0):
    mx, my = payload_mass_moment()
    return -mx / batt_m, mx / auw, my / auw

def rf_report(shift_x):
    """Мінімальні відстані від елементів Ягі до провідних тіл."""
    pts = []
    for z, L in yagi_elems():
        pts += seg_pts((YAGI["x"], YAGI["y"] - L / 2, z), (YAGI["x"], YAGI["y"] + L / 2, z))
    cond = {"рупор": d_horn, "батарея": lambda p: d_box(p, batt_box(shift_x)),
            "ZR10": lambda p: d_box(p, zr10_box()), "ретранслятор": lambda p: d_box(p, rep_box()),
            "нижня пластина CF": lambda p: d_box(p, PLATE_BOT)}
    for n, a, b, r, mat in segments():
        if mat == "CF":
            key = "ніжки CF" if n.startswith("ніжка") else "лижі CF"
            prev = cond.get(key)
            cond[key] = (lambda f, a=a, b=b, r=r: (lambda p: min(f(p), d_seg(p, a, b) - r)))(prev or (lambda p: 1e9))
    out = {}
    for k, f in cond.items():
        out[k] = min(f(p) for p in pts) - 3.0          # 3 мм — радіус елемента
    return out

def zr10_box():
    return dict(x0=ZR10["x"] - ZR10["w"] / 2, x1=ZR10["x"] + ZR10["w"] / 2, y0=ZR10["y"] - ZR10["w"] / 2, y1=ZR10["y"] + ZR10["w"] / 2,
                z0=ZR10["top"] - ZR10["h"], z1=ZR10["top"])

def rep_box():
    return dict(x0=REP["x"] - REP["lx"] / 2, x1=REP["x"] + REP["lx"] / 2, y0=REP["y"] - REP["ly"] / 2, y1=REP["y"] + REP["ly"] / 2,
                z0=REP["top"] - REP["h"], z1=REP["top"])

def mech_report(shift_x, ground=None):
    """Механічні зазори між тілами (мм) і просвіт над землею."""
    ground = LEG_BOT[2] - R_T if ground is None else ground
    bodies = {"рупор": ("horn", None), "ZR10": ("box", zr10_box()), "ретранслятор": ("box", rep_box()),
              "батарея": ("box", batt_box(shift_x)), "плита рупора": ("box", P_HORN), "плита ZR10": ("box", P_ZR10)}
    yagi_pts = []
    for z, L in yagi_elems():
        yagi_pts += seg_pts((YAGI["x"], YAGI["y"] - L / 2, z), (YAGI["x"], YAGI["y"] + L / 2, z))
    yagi_pts += seg_pts((YAGI["x"], YAGI["y"], YAGI["top"]), (YAGI["x"], YAGI["y"], YAGI["top"] - YAGI["boom"]))
    res = []
    for n, a, b, r, mat in segments():
        pts = seg_pts(a, b, 4.0)
        for bn, (kind, B) in bodies.items():
            if (n.startswith("рейка") and bn in ("плита рупора", "плита ZR10")) or (n.startswith("поперечка") and bn == "ретранслятор"):
                continue                                  # це кріплення, а не зіткнення
            d = min((d_horn(p) if kind == "horn" else d_box(p, B)) for p in pts) - r
            res.append((n, bn, d))
        d = min(min(d_seg(p, a, b) for p in yagi_pts[::3]) - r - 3, 999)
        if not (n == "поперечка X1"):
            res.append((n, "Ягі", d))
    clear = {"рупор": HORN["top"] - HORN["L"] - ground, "ZR10": zr10_box()["z0"] - ground,
             "Ягі": YAGI["top"] - YAGI["boom"] - ground, "ретранслятор": rep_box()["z0"] - ground}
    return res, clear


# ================= плити клітки: контур, отвори, вирізи =================
from shapely.geometry import Point, box as sbox
from shapely.ops import unary_union
M3, M4 = 3.2, 4.2
SADDLE_PITCH = 28.0            # сідло Ø16: 2×M3 поперек труби

def _rr(x0, x1, y0, y1, r):
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 32)

def _slot_x(cx, cy, L, W):     # паз уздовж x
    return sbox(cx - (L - W) / 2, cy, cx + (L - W) / 2, cy).buffer(W / 2, 32)

def cage_plates():
    """name -> dict(P=габарит, t, mat, outline=(x0,x1,y0,y1,r), holes=[(x,y,d,група)], cut=[(тип, параметри, група)])"""
    out = {}
    # плита рупора — лежить на рейках, горловина проходить між ними
    P = P_HORN; H = []
    for x in (P["x0"] + 15, P["x1"] - 15):
        for sy in (-1, 1):
            for dy in (-SADDLE_PITCH / 2, SADDLE_PITCH / 2):
                H.append((x, sy * RAIL_Y + dy, M3, "сідла на рейки"))
    cut = [("rrect", (HORN["x"] - 25, HORN["x"] + 25, -45.0, 45.0, 6.0), "горловина / адаптер")]
    out["horn"] = dict(P=P, t=3.0, mat="CF", outline=(P["x0"], P["x1"], P["y0"], P["y1"], 6.0), holes=H, cut=cut,
                       title="Плита рупора", note="CF 3 мм · лежить на рейках · отвори фланця рупора — по місцю")
    # плита ZR10 — під рейками
    P = P_ZR10; H = []
    for x in (P["x0"] + 15, P["x1"] - 15):
        for sy in (-1, 1):
            for dy in (-SADDLE_PITCH / 2, SADDLE_PITCH / 2):
                H.append((x, sy * RAIL_Y + dy, M3, "сідла на рейки"))
    cut = [("circle", (ZR10["x"], ZR10["y"], 15.0), "кабель ZR10")]
    out["zr10"] = dict(P=P, t=2.0, mat="CF", outline=(P["x0"], P["x1"], P["y0"], P["y1"], 6.0), holes=H, cut=cut,
                       title="Плита ZR10", note="CF 2 мм · під рейками · кріплення SIYI — за шаблоном з комплекту")
    # лоток ретранслятора — під поперечками X1/X2
    P = T_REP; H = []
    for name, (x, _) in XBARS.items():
        for dx in (-SADDLE_PITCH / 2, SADDLE_PITCH / 2):
            for y in (64.0, 156.0):
                H.append((x + dx, y, M3, f"сідла на {name}"))
    cut = [("slot", (xc, yc, 27.0, 5.0), "ремені 25 мм") for xc in (-5.0, 65.0) for yc in (50.0, 170.0)]
    out["tray"] = dict(P=P, t=2.0, mat="G10", outline=(P["x0"], P["x1"], P["y0"], P["y1"], 6.0), holes=H, cut=cut,
                       title="Лоток ретранслятора", note="G10 2 мм · під X1/X2 · короб на двох ременях 25 мм")
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
    ("J5", "Сідло Ø16", 12, 3, "PETG", "2×M3 крок 28: 4 рупор, 4 ZR10, 4 лоток"),
    ("J6", "Затискач бума Ягі", 1, 12, "PETG", "на X1; без вуглецевого наповнювача"),
    ("J7", "Заглушка лижі", 4, 2, "PETG", "")]
FASTENERS_G = 40

def cage_mass():
    t = sum(tube_kg_per_m(m) * L / 1000 * n for _, _, m, L, n in tubes()) * 1000
    j = sum(n * g for _, _, n, g, _, _ in JOINTS)
    p = sum(check_plate(pl)[1] for pl in cage_plates().values())
    return dict(tubes=t, joints=j, plates=p, fasteners=FASTENERS_G, total=t + j + p + FASTENERS_G)
