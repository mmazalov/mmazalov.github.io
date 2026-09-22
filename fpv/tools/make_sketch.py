"""Ескіз загального вигляду квадрокоптера 28" (3 аркуші A3) -> fpv/frame-sketch.pdf

Усі розміри в мм. Перезапуск: python3 fpv/tools/make_sketch.py
"""
import math, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
sys.path.insert(0, os.path.dirname(__file__))
import plate_geometry as G
import cage_geometry as C

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

OUT = os.path.join(os.path.dirname(__file__), "..", "frame-sketch.pdf")
W, H = 420, 297
INK, DIM, MUT = "#1a1a1a", "#c02020", "#8c8c8c"
ACC, SLC, CAM, RFC, PWR = "#0b6fb8", "#0e8a4f", "#b8560b", "#6b3fa0", "#c2410c"
DATE = "22.09.2026"

# ---------------- геометрія (мм) ----------------
BASE = 1150.0
R = BASE / 2                       # радіус мотора
D45 = R / math.sqrt(2)             # 406.6
PROP_R = 28 * 25.4 / 2             # 355.6
ARM_D = 50.0
PLATE = G.PLATE                    # центральна пластина — з plate_geometry.py
MOTOR_D = 69.0
SL_W, SL_H = 298.5, 259.0
GPS_FWD = -230.0
SHIFT = 0.0                        # касета в номінальному положенні; хід ±C.BATT_TRIM
BATT_X0 = C.BATT["x0"]
GROUND = C.GROUND                  # низ лиж
Z = dict(prop=0, sl_top=-6, sl_bot=-44.5, top=-55, arm=-80, bot=-105, bat=-171,
         rail=C.Z_RAIL, skid=C.LEG_BOT[2], gps=145)
LEG_TOP = (C.LEG_TOP[0], C.LEG_TOP[1])
LEG_BOT = (C.LEG_BOT[0], C.LEG_BOT[1])
RAIL_Y = C.RAIL_Y
BASE = C.base_kg()
AUW0 = BASE + C.BATT_KG            # без навісного
perf = C.perf

def mz(v): return f"{v:.0f}".replace("-", "−") if v < 0 else (f"+{v:.0f}" if v > 0 else "0")

def zone_tag(x, y, k, col, size=7):
    circ(x, y, 2.6, 0.35, col, "#ffffff", 1); tx(x, y - 1.05, k, size, True, col, "c")

def draw_zones(view, s, ox, oy, which="ABCD", tags=True):
    """Зони навісного в одній із проекцій: plan (ніс угору), side (ніс праворуч), front (правий борт ліворуч)."""
    seen = set()
    for k, bx in C.zone_boxes():
        if k not in which: continue
        col = C.ZONES[k]["col"]; x0, x1, y0, y1, z0, z1 = bx
        if view == "plan": X0, X1, Y0, Y1 = ox + y0 * s, ox + y1 * s, oy + x0 * s, oy + x1 * s
        elif view == "side": X0, X1, Y0, Y1 = ox + x0 * s, ox + x1 * s, oy + z0 * s, oy + z1 * s
        else: X0, X1, Y0, Y1 = ox - y1 * s, ox - y0 * s, oy + z0 * s, oy + z1 * s
        key = (round(X0), round(X1), round(Y0), round(Y1))
        rect(X0, Y0, X1 - X0, Y1 - Y0, 0.3, col, col, 0.06, dash=(2, 1.2))
        if tags and key not in seen:
            lbl = k if view != "front" or k == "D" else "A B C"
            if view == "front" and k != "D":
                for i_, kk in enumerate("ABC"): zone_tag(X0 + 6 + i_ * 6.5, Y1 - 5, kk, C.ZONES[kk]["col"], 6.5)
            else:
                zone_tag((X0 + X1) / 2, (Y0 + Y1) / 2 if view != "plan" else Y1 - 5, k, col)
        seen.add(key)

def zone_top(view, s, ox, oy):
    x0, x1, y0, y1, z0, z1 = C.ZONES["T"]["box"]; col = C.ZONES["T"]["col"]
    if view == "side": rect(ox + x0 * s, oy + z0 * s, (x1 - x0) * s, (z1 - z0) * s, 0.35, col, col, 0.08, dash=(2, 1.2))
    else: rect(ox - y1 * s, oy + z0 * s, (y1 - y0) * s, (z1 - z0) * s, 0.35, col, col, 0.08, dash=(2, 1.2))

# ---------------- примітиви ----------------
def new_canvas(path, title):
    global c
    c = canvas.Canvas(path, pagesize=(W * mm, H * mm)); c.setTitle(title); c.setAuthor("mmazalov")
    return c

c = new_canvas(OUT, "Ескіз загального вигляду · квадрокоптер 28\"")

def hx(s): return HexColor(s)

def _dash(dash):
    if dash: c.setDash(list(dash), 0)
    else: c.setDash()

def ln(x1, y1, x2, y2, w=0.3, col=INK, dash=None):
    c.setStrokeColor(hx(col)); c.setLineWidth(w * mm)
    _dash(dash)
    c.line(x1 * mm, y1 * mm, x2 * mm, y2 * mm)
    c.setDash()

def rect(x, y, w, h, lw=0.35, col=INK, fill=None, alpha=0.12, dash=None, r=0):
    c.setStrokeColor(hx(col)); c.setLineWidth(lw * mm)
    _dash(dash)
    if fill:
        c.setFillColor(hx(fill)); c.setFillAlpha(alpha)
    if r:
        c.roundRect(x * mm, y * mm, w * mm, h * mm, r * mm, stroke=1, fill=1 if fill else 0)
    else:
        c.rect(x * mm, y * mm, w * mm, h * mm, stroke=1, fill=1 if fill else 0)
    c.setFillAlpha(1); c.setDash()

def poly(pts, lw=0.35, col=INK, fill=None, alpha=0.12, dash=None):
    c.setStrokeColor(hx(col)); c.setLineWidth(lw * mm)
    _dash(dash)
    p = c.beginPath(); p.moveTo(pts[0][0] * mm, pts[0][1] * mm)
    for x, y in pts[1:]: p.lineTo(x * mm, y * mm)
    p.close()
    if fill: c.setFillColor(hx(fill)); c.setFillAlpha(alpha)
    c.drawPath(p, stroke=1, fill=1 if fill else 0)
    c.setFillAlpha(1); c.setDash()

def circ(x, y, r, lw=0.35, col=INK, fill=None, alpha=0.12, dash=None):
    c.setStrokeColor(hx(col)); c.setLineWidth(lw * mm)
    _dash(dash)
    if fill: c.setFillColor(hx(fill)); c.setFillAlpha(alpha)
    c.circle(x * mm, y * mm, r * mm, stroke=1, fill=1 if fill else 0)
    c.setFillAlpha(1); c.setDash()

def tx(x, y, s, size=8, bold=False, col=INK, anchor="l", angle=0):
    c.saveState(); c.setFillColor(hx(col)); c.setFont("DVB" if bold else "DV", size)
    c.translate(x * mm, y * mm); c.rotate(angle)
    {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[anchor](0, 0, s)
    c.restoreState()

def arrowhead(x, y, ux, uy, col=DIM, L=2.2, hw=0.6):
    nx, ny = -uy, ux
    poly([(x, y), (x - ux * L + nx * hw, y - uy * L + ny * hw),
          (x - ux * L - nx * hw, y - uy * L - ny * hw)], lw=0.05, col=col, fill=col, alpha=1)

def dim(x1, y1, x2, y2, label, off, size=7, col=DIM, tside=1):
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    s = 1 if off >= 0 else -1
    a1 = (x1 + nx * off, y1 + ny * off); a2 = (x2 + nx * off, y2 + ny * off)
    ln(x1 + nx * s * 0.8, y1 + ny * s * 0.8, a1[0] + nx * s * 1.5, a1[1] + ny * s * 1.5, 0.13, col)
    ln(x2 + nx * s * 0.8, y2 + ny * s * 0.8, a2[0] + nx * s * 1.5, a2[1] + ny * s * 1.5, 0.13, col)
    ln(*a1, *a2, 0.18, col)
    arrowhead(*a1, -ux, -uy, col); arrowhead(*a2, ux, uy, col)
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90.1: ang -= 180
    if ang <= -90: ang += 180
    mx, my = (a1[0] + a2[0]) / 2, (a1[1] + a2[1]) / 2
    k = 1.2 if s * tside > 0 else -(size * 0.35 + 1.2)
    tx(mx + nx * s * k, my + ny * s * k, label, size, True, col, "c", ang)

def leader(x1, y1, x2, y2, label, size=7, col=INK, anchor="l"):
    ln(x1, y1, x2, y2, 0.15, col); circ(x1, y1, 0.45, 0.1, col, col, 1)
    tx(x2 + (1 if anchor == "l" else -1), y2 - 1, label, size, False, col, anchor)

def sheet(n, total, title, scale, notes=None):
    rect(20, 10, 390, 277, lw=0.6)
    rect(280, 10, 130, 40, lw=0.5)
    for y in (20, 30, 40): ln(280, y, 410, y, 0.25)
    ln(345, 10, 345, 40, 0.25)
    tx(283, 43.5, "Квадрокоптер 28\" · база 1150 мм", 9.5, True)
    tx(283, 33, title, 8.5, True)
    tx(283, 23, f"Масштаб {scale}", 7.5); tx(348, 23, f"Аркуш {n} з {total}", 7.5)
    tx(283, 13, f"Дата {DATE}", 7.5); tx(348, 13, "ЕСКІЗ · не для виробництва", 6.8, True, DIM)
    tx(24, 281, "Розміри в мм · z = 0 — площина гвинтів · x — вперед (ніс), y — праворуч", 7, False, MUT)


def balloon(n, ax, ay, bx, by, col=INK):
    dx, dy = ax - bx, ay - by; L = math.hypot(dx, dy) or 1
    ln(ax, ay, bx + dx / L * 3, by + dy / L * 3, 0.15, col)
    circ(ax, ay, 0.5, 0.1, col, col, 1)
    circ(bx, by, 3, 0.3, col, "#ffffff", 1)
    tx(bx, by - 1.1, str(n), 7.5, True, col, "c")

TOTAL = 4
PARTS = [
    (1, "Гвинт 28\" складаний CF, 2 лоп.", "4"), (2, "Мотор T-Motor MN6012 KV170", "4"),
    (3, "Промінь CF Ø50×2 UD, L 555", "4"), (4, "Пластина верхня CF 2 мм 250×250", "1"),
    (5, "Пластина нижня CF 2 мм 250×250", "1"), (6, "Зона T — верхнє навісне, 4×M4", "—"),
    (7, "Pixhawk 6X + RPi CM4 baseboard", "1"), (8, "Батарея 12S1P у касеті G10", "1"),
    (9, "Щогла GPS, h 200", "1"), (10, "Рейки й поперечки G10 Ø16×14", "4"),
    (11, f"Ніжка клітки CF Ø16×14, L {C.LEG_CUT}", "4"), (12, "Лижа CF Ø16, L 600", "2"),
    (13, "Монтажна плита між рейками, CF 2", "за потр."), (14, "Монтажна плита бортова, G10 2", "за потр."),
]

def horn_shape(cx, z_top, z_bot, w_ap, w_throat, s, oxp, oyp, col, dash=None, fx=1):
    pts = [(oxp + (cx - w_throat / 2) * s * fx, oyp + z_top * s), (oxp + (cx + w_throat / 2) * s * fx, oyp + z_top * s),
           (oxp + (cx + w_ap / 2) * s * fx, oyp + z_bot * s), (oxp + (cx - w_ap / 2) * s * fx, oyp + z_bot * s)]
    poly(pts, 0.35, col, col, 0.08, dash)

# ================================================================
# АРКУШ 1 — вид зверху, М 1:6
# ================================================================
def sheet1():
    s = 1 / 6; ox, oy = 150, 148
    def T(f, r): return ox + r * s, oy + f * s
    sheet(1, TOTAL, "Вид зверху", "1:6")
    tx(24, 274, "ВИД ЗВЕРХУ", 12, True)
    motors = [("M1", D45, D45, "CCW"), ("M2", -D45, -D45, "CCW"),
              ("M3", D45, -D45, "CW"), ("M4", -D45, D45, "CW")]
    for _, f, r, _ in motors:
        circ(*T(f, r), PROP_R * s, 0.25, MUT, dash=(4, 2.5))
    for _, f, r, _ in motors:
        ang = math.atan2(f, r); ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
        a0 = PLATE / 2 * 0.95; hw = ARM_D / 2 * s
        (x0, y0), (x1, y1) = T(f * a0 / R, r * a0 / R), T(f, r)
        poly([(x0 + nx * hw, y0 + ny * hw), (x1 + nx * hw, y1 + ny * hw),
              (x1 - nx * hw, y1 - ny * hw), (x0 - nx * hw, y0 - ny * hw)], 0.35, INK, INK, 0.18)
    draw_zones("plan", s, ox, oy, tags=False)
    rect(ox - PLATE * s / 2, oy - PLATE * s / 2, PLATE * s, PLATE * s, 0.5, INK, "#ffffff", 0.9)
    circ(ox, oy, 195 * s, 0.45, SLC, SLC, 0.1, dash=(2.5, 1.5))
    c.saveState(); c.translate(ox * mm, oy * mm); c.rotate(45)
    c.setStrokeColor(hx(SLC)); c.setLineWidth(0.2 * mm); c.setDash([1, 1], 0)
    c.rect(-SL_W * s / 2 * mm, -SL_H * s / 2 * mm, SL_W * s * mm, SL_H * s * mm, 1, 0)
    c.restoreState(); c.setDash()
    tx(ox, oy + 1, "зона T", 7.5, True, SLC, "c"); tx(ox, oy - 3, "R195 · h 44", 6.5, False, SLC, "c")
    gx, gy = T(GPS_FWD, 0)
    ln(ox, oy - PLATE * s / 2, gx, gy, 0.8, ACC); circ(gx, gy, 2.2, 0.3, ACC, ACC, 0.9)
    leader(gx, gy, gx + 19, gy - 8, "GPS, щогла 200 мм", 7, ACC)
    for name, f, r, rot in motors:
        x, y = T(f, r); circ(x, y, MOTOR_D * s / 2, 0.45, INK, "#ffffff", 1)
        tx(x, y - 1.2, name, 7, True, INK, "c")
        tx(x, y - PROP_R * s + 3, rot, 7, True, MUT, "c")
    tx(ox, 266, "НІС", 10, True, INK, "c")
    poly([(ox, 277), (ox - 2.5, 272), (ox + 2.5, 272)], 0.1, INK, INK, 1)
    (x1, y1), (x2, y2) = T(D45, -D45), T(D45, D45)
    dim(x1, y1, x2, y2, "мотор–мотор 813", 14)
    xa, _ = T(D45, -D45 + PROP_R); xb, _ = T(D45, D45 - PROP_R)
    dim(xa, y1, xb, y1, "зазор 102", 5)
    (x1, y1), (x2, y2) = T(-PLATE / 2, -PLATE / 2), T(PLATE / 2, -PLATE / 2)
    dim(x1, y1, x2, y2, "250", 5)
    tx(196, 146.5, "база 1150 — діагональ M2–M1", 7.5, True, DIM)
    ax_, ay_ = T(-D45 * 0.6, -D45 * 0.6)
    leader(ax_, ay_, 105, 147.5, "промінь Ø50×2 UD, L 555", 7, INK, "r")
    mx, my = T(-D45, D45); a = math.radians(-25)
    leader(mx + PROP_R * s * math.cos(a), my + PROP_R * s * math.sin(a), 284, 100, "гвинт Ø711 (28\")", 7.5, MUT)
    X = 288; Y = 272
    tx(X, Y, "Основні параметри", 10, True); Y -= 8
    rows = [("База (мотор–мотор по діагоналі)", "1150"), ("Мотор–мотор (сусідні)", "813"),
            ("Гвинт", "28\" складаний CF"), ("Зазор між гвинтами", "102 (14 % D)"),
            ("Внутрішній досяг гвинта", "219"), ("Промінь", "Ø50×2, UD"),
            ("Центральні пластини", "250×250, CF 2 мм ×2"), ("Мотори", "MN6012 KV170"),
            ("Без навісного, з батареєю 5.0 кг", f"{AUW0:.1f} кг"), ("Висіння без навісного, 1500 м", f"≈ {perf(AUW0)[1]:.0f} хв"),
            ("Бюджет навісного до T/W 2.0", f"до {C.payload_max():.1f} кг")]
    for k, v in rows:
        tx(X, Y, k, 7, False, MUT); tx(406, Y, v, 7, True, INK, "r"); Y -= 5.2
    Y -= 4; tx(X, Y, "Порядок моторів — ArduCopter Quad X", 8.5, True); Y -= 6.5
    for t in ("M1 правий передній · CCW", "M2 лівий задній · CCW",
              "M3 лівий передній · CW", "M4 правий задній · CW",
              "Напрям обертання звірити в Mission Planner", "до встановлення гвинтів."):
        tx(X, Y, t, 7); Y -= 4.8
    Y -= 4; tx(X, Y, "Позначення", 8.5, True); Y -= 6.5
    for col, t in ((MUT, "диск гвинта"), (SLC, "зона T — над верхньою пластиною"),
                   (ACC, "GPS на щоглі"), (C.ZONES["B"]["col"], "зони A–D під рамою (пунктир)"),
                   (C.ZONES["A"]["col"], "деталі зон — cage-drawings.pdf")):
        rect(X, Y - 0.8, 5, 3, 0.3, col, col, 0.25); tx(X + 7, Y, t, 7); Y -= 5.2
    Y -= 3
    for t in ("Прямокутне в зоні T (напр. 298×259) заходить",
              "кутами в диск гвинта — ставити з поворотом 45°.",
              "Щогла GPS на осі корми: запас до диска 90 мм."):
        tx(X, Y, t, 6.8, False, DIM); Y -= 4.6
    c.showPage()

# ================================================================
# АРКУШ 2 — вид збоку, М 1:5
# ================================================================
def sheet2():
    s = 0.2; ox, oy = 176, 222
    def S(x, z): return ox + x * s, oy + z * s
    sheet(2, TOTAL, "Вид збоку", "1:5")
    tx(24, 274, "ВИД ЗБОКУ", 12, True); tx(24, 268, "з правого борту · ніс праворуч", 7, False, MUT)
    for sg in (-1, 1):
        ln(*S(sg * D45 - PROP_R, 0), *S(sg * D45 + PROP_R, 0), 0.9, MUT)
        mx, _ = S(sg * D45, 0); rect(mx - MOTOR_D * s / 2, oy + Z["top"] * s, MOTOR_D * s, -Z["top"] * s, 0.35, INK, "#ffffff", 1)
    rect(ox - D45 * s, oy + Z["bot"] * s, 2 * D45 * s, ARM_D * s, 0.3, INK, INK, 0.15)
    for zz in (Z["top"], Z["bot"]): rect(ox - PLATE / 2 * s, oy + zz * s - 0.4, PLATE * s, 0.8, 0.3, INK, INK, 1)
    slx = (SL_W / 2 + SL_H / 2) * math.cos(math.radians(45))
    zone_top("side", s, ox, oy)
    rect(ox - 55 * s, oy - 100 * s, 110 * s, 40 * s, 0.35, ACC, ACC, 0.12, dash=(2, 1.2))
    rect(ox + (BATT_X0 + SHIFT) * s, oy + Z["bat"] * s, 187 * s, (Z["bot"] - Z["bat"]) * s, 0.4, PWR, PWR, 0.12)
    for sg in (-1, 1): ln(*S(sg * LEG_TOP[0], C.LEG_TOP[2]), *S(sg * LEG_BOT[0], Z["skid"]), 1.1, INK)
    ln(*S(C.SKID_X[0], Z["skid"]), *S(C.SKID_X[1], Z["skid"]), 1.4, INK)
    ln(*S(C.RAIL_X[0], Z["rail"]), *S(C.RAIL_X[1], Z["rail"]), 0.9, INK)
    for _, (xb_, _) in C.XBARS.items(): circ(*S(xb_, C.Z_XBAR), 8 * s + 0.2, 0.35, INK, INK, 1)
    ln(*S(-560, GROUND), *S(560, GROUND), 0.2, MUT)
    for i in range(-27, 28):
        x0, y0 = S(i * 20, GROUND); ln(x0, y0, x0 - 1.5, y0 - 1.5, 0.12, MUT)
    draw_zones("side", s, ox, oy)
    gx, _ = S(GPS_FWD, 0)
    ln(gx, oy + Z["top"] * s, gx, oy + Z["gps"] * s, 0.6, ACC)
    rect(gx - 30 * s, oy + Z["gps"] * s, 60 * s, 15 * s, 0.3, ACC, ACC, 0.5)
    B = [(1, S(-600, 0), (40, 239)), (2, S(-406.6, -27), (70, 251)), (3, S(-300, -80), (95, 263)),
         (9, S(-230, 150), (122, 269)), (6, S(-120, -25), (150, 263)), (4, S(110, -55), (205, 263)),
         (7, S(40, -80), (230, 257)), (5, S(110, -105), (293, 207)), (8, S(70, -140), (293, 195)),
         (11, S(146, -470), (293, 139)), (12, S(260, Z["skid"]), (293, 123)), (10, S(-260, Z["rail"]), (40, 183))]
    for n, (ax, ay), (bx2, by2) in B: balloon(n, ax, ay, bx2, by2)
    dim(*S(700, GROUND), *S(700, Z["sl_top"]), f"{Z['sl_top'] - GROUND:.0f}", 0)
    dim(*S(770, GROUND), *S(770, Z["gps"]), f"{Z['gps'] - GROUND:.0f} з щоглою", 0)
    dim(*S(C.SKID_X[0], Z["skid"]), *S(C.SKID_X[1], Z["skid"]), f"лижа {C.SKID_X[1] - C.SKID_X[0]:.0f}", -9)
    X = 345; Y = 272
    tx(X, Y, "Рівні, z", 10, True); Y -= 7.5
    lv = [("GPS, верх", Z["gps"]), ("Гвинти", 0), ("Starlink, верх", Z["sl_top"]),
          ("Верхня пластина", Z["top"]), ("Вісь променя", Z["arm"]), ("Нижня пластина", Z["bot"]),
          ("Низ батареї", Z["bat"]), ("Рейки", C.Z_RAIL), ("Поперечки", C.Z_XBAR), ("Верх зон A–D", C.Z_TOP_ZONE),
          ("Низ зон A–D", C.Z_BOT_ZONE), ("Низ лиж", GROUND)]
    for k, v in lv:
        tx(X, Y, k, 7, False, MUT); tx(406, Y, mz(v), 7, True, INK, "r"); Y -= 5
    tx(24, 88, "Розв'язки", 9, True)
    notes = ["Зони навісного: A–D під рамою, T над верхньою пластиною. Габарити й правила — cage-drawings.pdf, аркуші 1–2.",
             "Клітка payload = шасі. Рейки й поперечки — площина кріплення, зони починаються під нею.",
             f"Просвіт під зонами {C.MIN_GROUND:.0f} мм; до ніжок, лиж і батареї — не менше 10 мм.",
             f"Касета батареї в пазах ±{C.BATT_TRIM:.0f} мм — балансування ЦМ під ваше навісне (±{C.BATT_KG * C.BATT_TRIM:.0f} кг·мм).",
             "Авіоніка між пластинами: промені займають лише 4 радіальні смуги, центр вільний, просвіт 50 мм."]
    Y = 81
    for t in notes: tx(24, Y, "• " + t, 7); Y -= 5
    c.showPage()

# ================================================================
# АРКУШ 3 — вид спереду + специфікація, М 1:5
# ================================================================
def sheet3():
    s = 0.2; ox, oy = 150, 215
    def F(y, z): return ox - y * s, oy + z * s
    sheet(3, TOTAL, "Вид спереду · специфікація", "1:5")
    tx(24, 274, "ВИД СПЕРЕДУ", 12, True); tx(24, 268, "з боку носа · промені обірвано", 7, False, MUT)
    rect(ox - 420 * s, oy + Z["bot"] * s, 840 * s, ARM_D * s, 0.3, INK, INK, 0.15)
    for sg in (-1, 1):
        xb = ox + sg * 420 * s
        for k in range(3):
            ln(xb + sg * (k % 2) * 1.2, oy + (Z["bot"] + k * 16.7) * s, xb + sg * ((k + 1) % 2) * 1.2, oy + (Z["bot"] + (k + 1) * 16.7) * s, 0.3, INK)
    for zz in (Z["top"], Z["bot"]): rect(ox - PLATE / 2 * s, oy + zz * s - 0.4, PLATE * s, 0.8, 0.3, INK, INK, 1)
    slx = (SL_W / 2 + SL_H / 2) * math.cos(math.radians(45))
    zone_top("front", s, ox, oy)
    rect(ox - 87 * s, oy + Z["bat"] * s, 174 * s, (Z["bot"] - Z["bat"]) * s, 0.4, PWR, PWR, 0.12)
    for sg in (-1, 1):
        ln(*F(sg * LEG_TOP[1], C.LEG_TOP[2]), *F(sg * LEG_BOT[1], Z["skid"]), 1.1, INK)
        circ(*F(sg * LEG_BOT[1], Z["skid"]), 8 * s + 0.3, 0.4, INK, INK, 1)
        circ(*F(sg * RAIL_Y, Z["rail"]), 8 * s + 0.2, 0.35, INK, INK, 1)
    y0_, y1_ = C.XBARS["X1"][1]
    ln(*F(y0_, C.Z_XBAR), *F(y1_, C.Z_XBAR), 1.1, INK)
    draw_zones("front", s, ox, oy)
    rect(ox - 95 * s, oy + (C.Z_RAIL - C.R_T - 2) * s, 190 * s, 2 * s + 0.3, 0.3, INK, INK, 0.7)
    for sg in (-1, 1):
        rect(ox + (sg * 150 - 75) * s, oy + (C.Z_XBAR - C.R_T - 2) * s, 150 * s, 2 * s + 0.3, 0.3, "#2e7d4f", "#2e7d4f", 0.7)
    ln(*F(560, GROUND), *F(-560, GROUND), 0.2, MUT)
    tx(ox - 290 * s - 6, oy + GROUND * s - 7, "ПРАВИЙ БОРТ", 7, True, MUT, "r")
    tx(ox + 290 * s + 6, oy + GROUND * s - 7, "ЛІВИЙ БОРТ", 7, True, MUT, "l")
    dim(*F(LEG_BOT[1], GROUND), *F(-LEG_BOT[1], GROUND), f"колія {2 * LEG_BOT[1]:.0f}", -9)
    B = [(6, F(150, -25), (95, 250)), (4, F(-110, -55), (180, 252)), (3, F(-350, -80), (238, 240)),
         (8, F(-60, -140), (245, 205)), (10, F(-RAIL_Y, Z["rail"]), (245, 187)), (13, F(-60, C.Z_RAIL - 11), (245, 170)),
         (14, F(-200, C.Z_XBAR - 11), (245, 152)), (11, F(156, -300), (60, 140)), (12, F(LEG_BOT[1], Z["skid"]), (60, 115))]
    for n, (ax, ay), (bx2, by2) in B: balloon(n, ax, ay, bx2, by2)
    X = 288; Y = 272
    tx(X, Y, "Специфікація", 10, True); Y -= 7
    tx(X, Y, "Поз.", 6.5, True, MUT); tx(X + 9, Y, "Найменування", 6.5, True, MUT); tx(406, Y, "К-сть", 6.5, True, MUT, "r"); Y -= 1.8
    ln(X, Y, 408, Y, 0.2, MUT); Y -= 4.2
    for n, name, q in PARTS:
        tx(X + 2, Y, str(n), 7, True); tx(X + 9, Y, name, 7); tx(406, Y, q, 7, False, INK, "r"); Y -= 5
    tx(24, 84, "Примітки", 9, True)
    notes = ["Зони A, B, C мають однаковий переріз у цьому виді; D — вузький коридор між ніжками (±75).",
             "Колія лиж 580 ≥ 550 — стійкість на ухилі з батареєю 5 кг під центром.",
             "Антени нижче 1 ГГц — у бортових частинах зон, ≥ λ/4 (83 мм на 900 МГц) від карбону й металу.",
             "Монтажні плити (поз. 13, 14) — приклади; кількість і положення — під ваше навісне."]
    Y = 77
    for t in notes: tx(24, Y, "• " + t, 7); Y -= 5
    c.showPage()

# ================================================================
# АРКУШ 4 — план payload М 1:4 + центральна пластина М 1:2
# ================================================================
def sheet4():
    sheet(4, TOTAL, "Зони встановлення · центральна пластина", "1:4 / 1:2")
    s = 0.25; ox, oy = 105, 160
    def T(f, r): return ox + r * s, oy + f * s
    tx(24, 274, "ЗОНИ ВСТАНОВЛЕННЯ — ПЛАН", 12, True); tx(24, 268, "проекція на вид зверху · рама фантомом", 7, False, MUT)
    rect(ox - PLATE / 2 * s, oy - PLATE / 2 * s, PLATE * s, PLATE * s, 0.25, MUT, dash=(2, 1.5))
    rect(ox - 87 * s, oy + BATT_X0 * s, 174 * s, 187 * s, 0.3, PWR, PWR, 0.08, dash=(2, 1.5))
    for sg in (-1, 1):
        ln(*T(-C.BATT_TRIM, 0 + sg * 60), *T(C.BATT_TRIM, 0 + sg * 60), 0.35, PWR)
        arrowhead(*T(C.BATT_TRIM, sg * 60), 0, 1, PWR, 1.4, 0.45); arrowhead(*T(-C.BATT_TRIM, sg * 60), 0, -1, PWR, 1.4, 0.45)
    tx(*T(-60, 0), f"касета ±{C.BATT_TRIM:.0f}", 6, True, PWR, "c")
    circ(ox, oy, C.PROP_SHADOW_R * s, 0.25, MUT, dash=(3, 2))
    tx(ox + C.PROP_SHADOW_R * s * 0.72, oy + C.PROP_SHADOW_R * s * 0.72 + 1, "тінь R219", 6, False, MUT)
    draw_zones("plan", s, ox, oy)
    for sg in (-1, 1):
        ln(*T(C.SKID_X[0], sg * LEG_BOT[1]), *T(C.SKID_X[1], sg * LEG_BOT[1]), 1.0, INK)
        ln(*T(C.RAIL_X[0], sg * RAIL_Y), *T(C.RAIL_X[1], sg * RAIL_Y), 0.7, "#2e7d4f")
        for sf in (-1, 1):
            circ(*T(sf * LEG_TOP[0], sg * LEG_TOP[1]), 1.1, 0.3, INK, INK, 1)
            ln(*T(sf * LEG_TOP[0], sg * LEG_TOP[1]), *T(sf * LEG_BOT[0], sg * LEG_BOT[1]), 0.6, INK)
    circ(ox, oy, 0.8, 0.2, INK, INK, 1)
    tx(ox, oy + 300 * s + 5, "НІС", 9, True, INK, "c")
    poly([(ox, oy + 300 * s + 11), (ox - 2, oy + 300 * s + 9), (ox + 2, oy + 300 * s + 9)], 0.1, INK, INK, 1)
    zA, zB, zC, zD = (C.ZONES[k]["box"] for k in "ABCD")
    dim(*T(zC[0], -300), *T(zA[1], -300), "580 (A–D уздовж)", 9, 6.3)
    dim(*T(-300, zB[2]), *T(-300, zB[3]), f"{zB[3] - zB[2]:.0f}", -6, 6.3)
    dim(*T(zB[0], 290), *T(zB[1], 290), f"B {zB[1] - zB[0]:.0f}", -3, 6)
    tx(24, 60, "Зони: A носова 123×544, B центральна 208×544, C кормова 123×544, D коридори 63×150 (×2); висота 288.", 7, False, INK)
    tx(24, 55, f"ЦМ: касета батареї в пазах ±{C.BATT_TRIM:.0f} мм компенсує ±{C.BATT_KG * C.BATT_TRIM:.0f} кг·мм по x. По y компенсації немає.", 7, False, DIM)
    # ---- пластина ----
    s2 = 0.5; px, py = 318, 172
    tx(215, 274, "ЦЕНТРАЛЬНА ПЛАСТИНА", 12, True)
    tx(215, 268, "CF 2 мм · 2 шт · вид зверху · для DXF брати розміри, не масштаб", 7, False, MUT)
    hp = PLATE / 2
    poly([(px + x * s2, py + y * s2) for x, y in list(G.outline_poly().exterior.coords)[:-1]], 0.5, INK, "#f2f2f2", 1)
    for a in (45, 135, 225, 315):
        ua = math.radians(a); ux, uy = math.cos(ua), math.sin(ua); nx, ny = -uy, ux
        cps = [(ux * al + nx * ac, uy * al + ny * ac) for al, ac in ((80, -38), (145, -38), (145, 38), (80, 38))]
        poly([(px + x * s2, py + y * s2) for x, y in cps], 0.25, MUT, MUT, 0.08, dash=(1.5, 1))
        ln(px + ux * 50 * s2, py + uy * 50 * s2, px + ux * 185 * s2, py + uy * 185 * s2, 0.15, MUT, dash=(4, 1.5, 1, 1.5))
    for sl in G.SLOTS:
        poly([(px + x * s2, py + y * s2) for x, y in list(G.slot_poly(*sl).exterior.coords)[:-1]], 0.3, INK, "#ffffff", 1)
    for sl in G.BATT_SLOTS:
        poly([(px + x * s2, py + y * s2) for x, y in list(G.vslot_poly(*sl).exterior.coords)[:-1]], 0.3, ACC, "#ffffff", 1)
    for layer, col, dy in (("T", SLC, 5), ("B", ACC, -1)):
        w, h, r = G.POCKET[layer]
        poly([(px + x * s2, py + y * s2) for x, y in list(G.rrect_poly(w, h, r).exterior.coords)[:-1]], 0.3, col, dash=(1.5, 1))
        tx(px, py + dy, f"виріз {'верх' if layer == 'T' else 'низ'} {w:.0f}×{h:.0f}", 5.5, False, col, "c")
    H = G.holes()
    lc = {"TB": INK, "T": SLC, "B": ACC}
    for x, y, d, layer, g in H:
        circ(px + x * s2, py + y * s2, d / 2 * s2 + 0.15, 0.28, lc[layer], "#ffffff", 1)
    tx(px, py + hp * s2 + 12, "НІС", 8, True, INK, "c")
    dim(px - hp * s2, py + hp * s2, px + hp * s2, py + hp * s2, "250", 6)
    dim(px + hp * s2, py - hp * s2, px + hp * s2, py + hp * s2, "250", -6)
    dim(px - 90 * s2, py - hp * s2, px + 90 * s2, py - hp * s2, "Starlink 180", -6, 6.5)
    tx(215, 98, "Отвори", 8.5, True)
    groups = {}
    for x, y, d, layer, g in H: groups[(g, layer, d)] = groups.get((g, layer, d), 0) + 1
    lname = {"TB": "обидві", "T": "верх", "B": "низ"}
    for i, ((g, layer, d), n) in enumerate(groups.items()):
        cx = 215 + (i // 4) * 98; cy = 92 - (i % 4) * 5
        circ(cx + 1.5, cy + 1, 1.3, 0.3, lc[layer], "#ffffff", 1)
        tx(cx + 4.5, cy, f"{n}× Ø{d} · {g} [{lname[layer]}]", 6.4)
    Y = 69
    mT, mB = G.mass_g(G.check("T")[1]), G.mass_g(G.check("B")[1])
    for t in ("Затискач Ø50: 4×M4, крок 40 уздовж × 64 впоперек. Пази 40×12 — під джгути.",
              f"Пластина 250×250 (на 210×200 затискачі Ø50 не поміщаються): верх {mT:.0f} г, низ {mB:.0f} г.",
              f"Нижня: 2 пази касети 60×4.2 під 2×M4 кожен — хід ±{C.BATT_TRIM:.0f} мм. Півкруглий виріз на кромці — ніс.",
              "DXF для різки: fpv/cnc/plate_top.dxf, plate_bottom.dxf."):
        tx(215, Y, t, 6.4, False, DIM if "Пластина" in t else INK); Y -= 4.4
    c.showPage()
    return H

if __name__ == "__main__":
    sheet1(); sheet2(); sheet3(); H = sheet4()
    c.save()
    probs = G.check("T")[0] + G.check("B")[0]
    print("Перевірка пластини:", "OK" if not probs else "\n  " + "\n  ".join(probs))
    print("PDF:", os.path.abspath(OUT))
