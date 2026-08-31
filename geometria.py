import json
import os

import numpy as np
import trimesh

BASE = os.path.dirname(os.path.abspath(__file__))

L, W, H = 3.20, 3.00, 3.00
PT, PW, PH = 0.05, 0.60, 1.20
TW, TH = 0.60, 1.20
LID_T = 0.012
CEIL = 0.42

PANELS = []
TRAPS = []


def add_panel(center, ext, rz=0.0, kind="panel"):
    PANELS.append({"type": kind, "center": [round(v, 4) for v in center],
                   "extents": [round(v, 4) for v in ext], "rz": rz})


def add_trap(x0, y0, sx, sy, z_mid, gid):
    """Prisma triangular de esquina: 2 tapas Δ + 2 tapas □ + volumen de lana."""
    z0 = round(z_mid - TH / 2, 4)
    z1 = round(z_mid + TH / 2, 4)
    x0, y0, sx, sy = float(x0), float(y0), float(sx), float(sy)

    base = [
        [round(x0, 4), round(y0, 4)],
        [round(x0 + sx * TW, 4), round(y0, 4)],
        [round(x0, 4), round(y0 + sy * TW, 4)],
    ]
    base_inner = [
        [round(x0 + sx * LID_T, 4), round(y0 + sy * LID_T, 4)],
        [round(x0 + sx * TW, 4), round(y0 + sy * LID_T, 4)],
        [round(x0 + sx * LID_T, 4), round(y0 + sy * TW, 4)],
    ]
    cx = round((base[0][0] + base[1][0] + base[2][0]) / 3, 4)
    cy = round((base[0][1] + base[1][1] + base[2][1]) / 3, 4)

    TRAPS.append({
        "type": "trap",
        "shape": "prism",
        "base": base_inner,
        "z0": round(z0 + LID_T, 4),
        "z1": round(z1 - LID_T, 4),
        "center": [cx, cy, round(z_mid, 4)],
        "extents": [TW, TW, TH],
        "rz": 0.0,
        "gid": gid,
    })
    TRAPS.append({
        "type": "trap_lid",
        "part": "rect",
        "center": [round(x0 + sx * TW / 2, 4), round(y0 + sy * LID_T / 2, 4), round(z_mid, 4)],
        "extents": [round(TW, 4), round(LID_T, 4), round(TH, 4)],
        "rz": 0.0,
        "gid": gid,
    })
    TRAPS.append({
        "type": "trap_lid",
        "part": "rect",
        "center": [round(x0 + sx * LID_T / 2, 4), round(y0 + sy * TW / 2, 4), round(z_mid, 4)],
        "extents": [round(LID_T, 4), round(TW, 4), round(TH, 4)],
        "rz": 0.0,
        "gid": gid,
    })
    for zlo, zhi in ((z0, z0 + LID_T), (z1 - LID_T, z1)):
        TRAPS.append({
            "type": "trap_lid",
            "part": "tri",
            "shape": "prism",
            "base": base,
            "z0": round(zlo, 4),
            "z1": round(zhi, 4),
            "center": [cx, cy, round((zlo + zhi) / 2, 4)],
            "extents": [TW, TW, LID_T],
            "rz": 0.0,
            "gid": gid,
        })


for yc in (0.6, 1.5, 2.4):
    add_panel([PT / 2, yc, 1.2], [PT, PW, PH])
    add_panel([L - PT / 2, yc, 1.2], [PT, PW, PH])

add_panel([2.2, PT / 2, 1.2], [PW, PT, PH])
add_panel([2.2, W - PT / 2, 1.2], [PW, PT, PH])
add_panel([1.4, PT / 2, 1.2], [PW, PT, PH])
add_panel([1.4, W - PT / 2, 1.2], [PW, PT, PH])

# Lado largo a lo ancho: si ambos clouds van 1,20 m en X se solapan 50 cm.
add_panel([1.6, 1.5, H - CEIL - 0.025], [0.6, 1.2, 0.05], kind="ceil")
add_panel([2.3, 1.5, H - CEIL - 0.025], [0.6, 1.2, 0.05], kind="ceil")

_tn = 0
for x0, y0, sx, sy in (
    (0.0, 0.0, 1.0, 1.0),
    (L, 0.0, -1.0, 1.0),
    (0.0, W, 1.0, -1.0),
    (L, W, -1.0, -1.0),
):
    _tn += 1
    add_trap(x0, y0, sx, sy, 0.75, "T{}".format(_tn))
    _tn += 1
    add_trap(x0, y0, sx, sy, 1.95, "T{}".format(_tn))

FURN = [
    {"type": "desk", "center": [L - 0.30, 1.5, 0.755], "extents": [0.60, 1.7, 0.05], "rz": 0.0, "color": "#b7b7b7"},
    {"type": "desk", "center": [L - 0.30, 0.85, 0.36], "extents": [0.55, 0.5, 0.72], "rz": 0.0, "color": "#a9a9a9"},
    {"type": "desk", "center": [L - 0.30, 2.15, 0.36], "extents": [0.55, 0.5, 0.72], "rz": 0.0, "color": "#a9a9a9"},
    {"type": "monitor", "center": [L - 0.52, 1.18, 0.99], "extents": [0.07, 0.46, 0.30], "rz": 0.0, "color": "#6f6f6f"},
    {"type": "monitor", "center": [L - 0.52, 1.18, 0.86], "extents": [0.12, 0.24, 0.14], "rz": 0.0, "color": "#8f8f8f"},
    {"type": "monitor", "center": [L - 0.52, 1.82, 0.99], "extents": [0.07, 0.46, 0.30], "rz": 0.0, "color": "#6f6f6f"},
    {"type": "monitor", "center": [L - 0.52, 1.82, 0.86], "extents": [0.12, 0.24, 0.14], "rz": 0.0, "color": "#8f8f8f"},
    {"type": "chair", "center": [1.9, 1.5, 0.45], "extents": [0.5, 0.5, 0.06], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.61, 1.5, 0.72], "extents": [0.08, 0.5, 0.55], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.9, 1.5, 0.16], "extents": [0.07, 0.07, 0.18], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.9, 1.5, 0.03], "extents": [0.4, 0.4, 0.04], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "window", "center": [1.7, W - 0.015, 1.5], "extents": [1.2, 0.02, 1.2], "rz": 0.0, "color": "#74b6d4"},
    {"type": "door", "center": [0.55, 0.015, 1.0], "extents": [0.8, 0.02, 2.0], "rz": 0.0, "color": "#b58b52"},
]

SHELL = [
    {"center": [L / 2, W / 2, -0.04], "extents": [L + 0.1, W + 0.1, 0.08], "rz": 0.0, "color": "#d0d0d0"},
    {"center": [0.025, W / 2, H / 2], "extents": [0.05, W + 0.05, H], "rz": 0.0, "color": "#c6c6c6"},
    {"center": [L - 0.025, W / 2, H / 2], "extents": [0.05, W + 0.05, H], "rz": 0.0, "color": "#c6c6c6"},
    {"center": [L / 2, 0.025, H / 2], "extents": [L + 0.05, 0.05, H], "rz": 0.0, "color": "#c6c6c6"},
    {"center": [L / 2, W - 0.025, H / 2], "extents": [L + 0.05, 0.05, H], "rz": 0.0, "color": "#c6c6c6"},
]


def box_corners(center, extents, rz):
    half = np.array(extents) / 2.0
    t = np.radians(rz)
    c, s = np.cos(t), np.sin(t)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    local = [(bx, by, bz) for bx in (-half[0], half[0])
             for by in (-half[1], half[1]) for bz in (-half[2], half[2])]
    return R @ np.array(local).T + np.array(center)[:, None]


def trap_corners(box):
    pts = []
    for x, y in box["base"]:
        pts.append([x, y, box["z0"]])
        pts.append([x, y, box["z1"]])
    return np.array(pts).T


def item_corners(box):
    if box.get("shape") == "prism":
        return trap_corners(box)
    return box_corners(box["center"], box["extents"], box.get("rz", 0.0))


def export_desc():
    descs = []
    for p in PANELS:
        descs.append({"type": p["type"], "center": p["center"], "extents": p["extents"], "rz": p["rz"],
                      "color": "#16a2a2" if p["type"] == "panel" else "#3f9b5a"})
    for t in TRAPS:
        d = {
            "type": t["type"],
            "center": t["center"],
            "extents": t["extents"],
            "rz": t.get("rz", 0.0),
            "color": "#f08c0a" if t["type"] == "trap" else "#c9a227",
        }
        if t.get("part"):
            d["part"] = t["part"]
        if t.get("gid"):
            d["gid"] = t["gid"]
        if t.get("shape") == "prism":
            d["shape"] = "prism"
            d["base"] = t["base"]
            d["z0"] = t["z0"]
            d["z1"] = t["z1"]
        descs.append(d)
    for f in FURN:
        descs.append({"type": f["type"], "center": f["center"], "extents": f["extents"], "rz": f["rz"], "color": f["color"]})
    for s in SHELL:
        descs.append({"type": "wall", "center": s["center"], "extents": s["extents"], "rz": s["rz"], "color": s["color"]})
    return descs


def prism_trimesh(base, z0, z1):
    verts = [[x, y, z0] for x, y in base] + [[x, y, z1] for x, y in base]
    faces = [
        [0, 2, 1], [3, 4, 5],
        [0, 1, 4], [0, 4, 3],
        [1, 2, 5], [1, 5, 4],
        [2, 0, 3], [2, 3, 5],
    ]
    return trimesh.Trimesh(vertices=verts, faces=faces, process=True)


YUP = [[1.0, 0.0, 0.0, 0.0],
       [0.0, 0.0, 1.0, 0.0],
       [0.0, -1.0, 0.0, 0.0],
       [0.0, 0.0, 0.0, 1.0]]

scene = trimesh.Scene()
for d in export_desc():
    if d.get("shape") == "prism":
        m = prism_trimesh(d["base"], d["z0"], d["z1"])
    else:
        m = trimesh.creation.box(extents=d["extents"])
        t = np.radians(d["rz"])
        c, s = np.cos(t), np.sin(t)
        m.apply_transform([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        m.apply_translation(d["center"])
    m.apply_transform(YUP)
    rgb = (int(d["color"][1:3], 16) / 255, int(d["color"][3:5], 16) / 255, int(d["color"][5:7], 16) / 255)
    m.visual.vertex_colors = (*rgb, 1.0)
    scene.add_geometry(m)

scene.export(os.path.join(BASE, "modelo_acustico.glb"))
scene.export(os.path.join(BASE, "modelo_acustico.obj"))
with open(os.path.join(BASE, "modelo_acustico.json"), "w") as f:
    json.dump(export_desc(), f, indent=1)

n_fill = sum(1 for t in TRAPS if t["type"] == "trap")
n_lid = sum(1 for t in TRAPS if t["type"] == "trap_lid")
print("OK:", len(PANELS), "panels,", n_fill, "trampas,", n_lid, "tapas")
print("glb/obj/json exportados en", BASE)
