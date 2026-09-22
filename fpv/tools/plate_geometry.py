"""Геометрія центральних пластин — єдине джерело для PDF-ескізу і DXF.

Система координат: центр пластини (0, 0), x — праворуч, y — вперед (ніс), мм.
"""
import math
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

PLATE = 250.0          # квадрат 250×250
CHAMFER = 18.0         # фаски на кутах (там виходять промені)
THICK = 2.0            # CF, мм
DENSITY = 1.55         # г/см³
NOTCH_R = 2.5          # півкруглий виріз на передній кромці — орієнтир «ніс»
ARM_DIRS = (45, 135, 225, 315)
CLAMP_ALONG = (80.0, 145.0)   # зона затискача Ø50 уздовж променя
CLAMP_HALF = 38.0              # напівширина затискача
M4, M3 = 4.2, 3.2

def holes():
    """(x, y, d, шар, група); шар: TB — обидві пластини, T — верхня, B — нижня."""
    H = []
    for a in ARM_DIRS:
        ua = math.radians(a); ux, uy = math.cos(ua), math.sin(ua); nx, ny = -uy, ux
        for along in (90, 130):
            for ac in (-32, 32):
                H.append((ux * along + nx * ac, uy * along + ny * ac, M4, "TB", "затискачі променів"))
    for x, y in ((110, 0), (-110, 0), (0, 110), (0, -110)):
        H.append((x, y, M3, "TB", "стійки 50 мм"))
    for x in (-90, 90):
        for y in (-20, 20):
            H.append((x, y, M4, "T", "кронштейн Starlink"))
    for x in (-25, 25):
        H.append((x, -112, M4, "T", "кронштейн щогли GPS"))
    for x in (-55, 55):
        for y in (-40, 40):
            H.append((x, y, M3, "B", "демпфери Pixhawk"))
    for sy in (-1, 1):
        for x in (-50, -30, 30, 50):
            H.append((x, sy * 115, M4, "B", "ніжки клітки"))
    return H

# пази під джгути: (cx, cy, довжина, ширина) — прямі кінці скруглені повністю
SLOTS = [(0.0, 70.0, 40.0, 12.0), (0.0, -70.0, 40.0, 12.0)]
# пази касети батареї (лише нижня): уздовж ходу x — вперед/назад, 2×M4 у кожному, хід ±15 мм
BATT_SLOTS = [(-95.0, 0.0, 60.0, M4), (95.0, 0.0, 60.0, M4)]   # (cx, cy, довжина по y, ширина)
# центральні полегшувальні вирізи: (w, h, r) — прямокутник зі скругленнями
POCKET = {"T": (80.0, 80.0, 10.0), "B": (70.0, 50.0, 10.0)}

def outline_pts():
    hp, c = PLATE / 2, CHAMFER
    return [(-hp + c, -hp), (hp - c, -hp), (hp, -hp + c), (hp, hp - c),
            (hp - c, hp), (-hp + c, hp), (-hp, hp - c), (-hp, -hp + c)]

def outline_poly():
    return Polygon(outline_pts()).difference(Point(0, PLATE / 2).buffer(NOTCH_R, 32))

def slot_poly(cx, cy, L, W):
    return box(cx - (L - W) / 2, cy, cx + (L - W) / 2, cy).buffer(W / 2, 32)

def vslot_poly(cx, cy, L, W):
    return box(cx, cy - (L - W) / 2, cx, cy + (L - W) / 2).buffer(W / 2, 32)

def rrect_poly(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, 32)

def clamp_poly(a):
    ua = math.radians(a); ux, uy = math.cos(ua), math.sin(ua); nx, ny = -uy, ux
    a0, a1 = CLAMP_ALONG
    return Polygon([(ux * al + nx * ac, uy * al + ny * ac)
                    for al, ac in ((a0, -CLAMP_HALF), (a1, -CLAMP_HALF), (a1, CLAMP_HALF), (a0, CLAMP_HALF))])

def layer_holes(layer):
    return [h for h in holes() if h[3] in (layer, "TB")]

def check(layer, min_web=6.0, min_edge_k=1.5):
    """Перевірка пластини: край, перемички, затискачі, пази, виріз, зв'язність."""
    problems = []
    out = outline_poly()
    hs = layer_holes(layer)
    feats = [("паз", slot_poly(*s)) for s in SLOTS] + [("виріз", rrect_poly(*POCKET[layer]))]
    if layer == "B": feats += [("паз касети", vslot_poly(*s)) for s in BATT_SLOTS]
    clamps = [clamp_poly(a) for a in ARM_DIRS]
    for i, (x, y, d, _, g) in enumerate(hs):
        p = Point(x, y); hole = p.buffer(d / 2, 32)
        edge = out.exterior.distance(p) - d / 2
        if edge < max(min_edge_k * d, 6.0):
            problems.append(f"{layer}: {g} ({x:.0f},{y:.0f}) до краю {edge:.1f} мм")
        if g != "затискачі променів" and any(cp.intersects(hole) for cp in clamps):
            problems.append(f"{layer}: {g} ({x:.0f},{y:.0f}) під затискачем")
        for name, f in feats:
            w = f.distance(hole)
            if w < min_web:
                problems.append(f"{layer}: {g} ({x:.0f},{y:.0f}) до {name}у {w:.1f} мм")
        for (x2, y2, d2, _, _) in hs[i + 1:]:
            gap = math.hypot(x - x2, y - y2) - (d + d2) / 2
            if gap < min_web:
                problems.append(f"{layer}: ({x:.0f},{y:.0f})–({x2:.0f},{y2:.0f}) перемичка {gap:.1f} мм")
    for name, f in feats:
        if out.exterior.distance(f) < 10:
            problems.append(f"{layer}: {name} до краю < 10 мм")
        for cp in clamps:
            if cp.intersects(f):
                problems.append(f"{layer}: {name} заходить під затискач")
    material = out.difference(unary_union([f for _, f in feats] +
                                          [Point(x, y).buffer(d / 2, 32) for x, y, d, _, _ in hs]))
    if material.geom_type != "Polygon":
        problems.append(f"{layer}: пластина розпадається на {len(material.geoms)} частин")
    return problems, material

def mass_g(material):
    return material.area * THICK / 1000 * DENSITY
