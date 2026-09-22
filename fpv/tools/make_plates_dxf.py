"""DXF центральних пластин для CNC -> fpv/cnc/plate_top.dxf, plate_bottom.dxf

Одиниці — мм. Початок координат — лівий нижній кут габариту пластини.
Шари: CUT_OUTER — зовнішній контур, CUT_INNER — отвори, пази, вирізи.
Запуск: python3 fpv/tools/make_plates_dxf.py
"""
import math, os, sys
import ezdxf
from ezdxf import units
from shapely.geometry import Point, Polygon
from ezdxf import path as dxfpath
sys.path.insert(0, os.path.dirname(__file__))
import plate_geometry as G

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "cnc")
OFF = G.PLATE / 2          # зсув: центр пластини -> (125, 125)
B90 = math.tan(math.radians(90) / 4)   # bulge чверті кола

def P(x, y): return (x + OFF, y + OFF)

def outline(msp):
    hp, R = G.PLATE / 2, G.NOTCH_R
    pts = G.outline_pts()
    # передня кромка йде від (hp-c, hp) до (-hp+c, hp); вставляємо півкруглий виріз по центру
    seq = []
    for i, (x, y) in enumerate(pts):
        seq.append((*P(x, y), 0))
        nx_, ny_ = pts[(i + 1) % len(pts)]
        if y == hp and ny_ == hp and x > nx_:
            seq.append((*P(R, hp), -1))      # півколо всередину пластини (за годинниковою)
            seq.append((*P(-R, hp), 0))
    msp.add_lwpolyline(seq, format="xyb", close=True, dxfattribs={"layer": "CUT_OUTER"})

def slot(msp, cx, cy, L, W):
    a, r = (L - W) / 2, W / 2
    msp.add_lwpolyline([(*P(cx - a, cy - r), 0), (*P(cx + a, cy - r), 1),
                        (*P(cx + a, cy + r), 0), (*P(cx - a, cy + r), 1)],
                       format="xyb", close=True, dxfattribs={"layer": "CUT_INNER"})

def rrect(msp, w, h, r):
    a, b = w / 2, h / 2
    msp.add_lwpolyline([(*P(-a + r, -b), 0), (*P(a - r, -b), B90), (*P(a, -b + r), 0), (*P(a, b - r), B90),
                        (*P(a - r, b), 0), (*P(-a + r, b), B90), (*P(-a, b - r), 0), (*P(-a, -b + r), B90)],
                       format="xyb", close=True, dxfattribs={"layer": "CUT_INNER"})

def build(layer, name):
    doc = ezdxf.new("R2000", setup=True)
    doc.units = units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT_OUTER", color=7)
    doc.layers.add("CUT_INNER", color=1)
    msp = doc.modelspace()
    outline(msp)
    for x, y, d, _, _ in G.layer_holes(layer):
        msp.add_circle(P(x, y), d / 2, dxfattribs={"layer": "CUT_INNER"})
    for s in G.SLOTS: slot(msp, *s)
    rrect(msp, *G.POCKET[layer])
    path = os.path.join(OUT_DIR, name)
    doc.saveas(path)
    return path

def verify(path, layer):
    doc = ezdxf.readfile(path)
    auditor = doc.audit()
    msp = doc.modelspace()
    circles = msp.query("CIRCLE"); polys = msp.query("LWPOLYLINE")
    exp_h = len(G.layer_holes(layer))
    outer = [p for p in polys if p.dxf.layer == "CUT_OUTER"]
    xs, ys = [], []
    for e in msp:
        for v in (e.vertices_in_wcs() if e.dxftype() == "LWPOLYLINE" else [e.dxf.center]):
            xs.append(v[0]); ys.append(v[1])
    shape = G.outline_poly()
    outside = [c for c in circles if not shape.buffer(-0.01).contains(Point(c.dxf.center[0] - OFF, c.dxf.center[1] - OFF).buffer(c.dxf.radius))]
    # площі контурів з DXF (дуги розгорнуті) проти еталонної геометрії — ловить невірний знак bulge
    def area(e): return Polygon([(v.x, v.y) for v in dxfpath.make_path(e).flattening(0.01)]).area
    ref = {"CUT_OUTER": [G.outline_poly().area]}
    ref["CUT_INNER"] = sorted([G.slot_poly(*sl).area for sl in G.SLOTS] + [G.rrect_poly(*G.POCKET[layer]).area])
    got_o = [area(p) for p in polys if p.dxf.layer == "CUT_OUTER"]
    got_i = sorted(area(p) for p in polys if p.dxf.layer == "CUT_INNER")
    area_ok = (len(got_i) == len(ref["CUT_INNER"])
               and all(abs(a - b) / b < 0.002 for a, b in zip(got_o + got_i, ref["CUT_OUTER"] + ref["CUT_INNER"])))
    print(f"    площі: контур {got_o[0]:.1f} / {ref['CUT_OUTER'][0]:.1f} мм², "
          f"пази і виріз {[round(a) for a in got_i]} / {[round(a) for a in ref['CUT_INNER']]} -> {'OK' if area_ok else 'FAIL'}")
    ok = (area_ok and not auditor.has_errors and len(circles) == exp_h and len(outer) == 1
          and all(p.closed for p in polys) and not outside)
    print(f"  {os.path.basename(path)}: отворів {len(circles)}/{exp_h}, контурів {len(polys)}, "
          f"габарит {max(xs)-min(xs):.1f}×{max(ys)-min(ys):.1f} мм, аудит {'OK' if not auditor.has_errors else 'ПОМИЛКИ'}"
          f"{'' if not outside else f', поза контуром: {len(outside)}'} -> {'OK' if ok else 'FAIL'}")
    return ok

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    allok = True
    for layer, name in (("T", "plate_top.dxf"), ("B", "plate_bottom.dxf")):
        probs, material = G.check(layer)
        print(f"{name}: перевірка геометрії {'OK' if not probs else probs}, маса {G.mass_g(material):.0f} г")
        allok &= not probs
        allok &= verify(build(layer, name), layer)
    sys.exit(0 if allok else 1)
