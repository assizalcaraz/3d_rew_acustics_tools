import json
import os

import numpy as np
import trimesh

BASE = os.path.dirname(os.path.abspath(__file__))

L, W, H = 3.20, 3.00, 3.00
PT, PW, PH = 0.05, 0.60, 1.20
TT, TW, TH = 0.10, 0.60, 1.20
CEIL = 0.42

PANELS = []
TRAPS = []


def add_panel(center, ext, rz=0.0, kind="panel"):
    PANELS.append({"type": kind, "center": [round(v, 4) for v in center],
                   "extents": [round(v, 4) for v in ext], "rz": rz})


def add_trap(center, rz):
    TRAPS.append({"type": "trap", "center": [round(v, 4) for v in center],
                  "extents": [round(TW / np.sin(np.pi / 4), 4), TT, TH], "rz": rz})


for yc in (0.6, 1.5, 2.4):
    add_panel([PT / 2, yc, 1.2], [PT, PW, PH])
    add_panel([L - PT / 2, yc, 1.2], [PT, PW, PH])

add_panel([2.2, PT / 2, 1.2], [PW, PT, PH])
add_panel([2.2, W - PT / 2, 1.2], [PW, PT, PH])
add_panel([1.4, PT / 2, 1.2], [PW, PT, PH])
add_panel([1.4, W - PT / 2, 1.2], [PW, PT, PH])

add_panel([1.6, 1.5, H - CEIL - 0.025], [1.2, 0.6, 0.05], kind="ceil")
add_panel([2.3, 1.5, H - CEIL - 0.025], [1.2, 0.6, 0.05], kind="ceil")

corners = [(0.0, 0.0, -45.0), (L, 0.0, 45.0), (0.0, W, 45.0), (L, W, 135.0)]
centers = [(0.3, 0.3), (L - 0.3, 0.3), (0.3, W - 0.3), (L - 0.3, W - 0.3)]
for (cx, cy, rz), (mx, my) in zip(corners, centers):
    add_trap([mx, my, 0.75], rz)
    add_trap([mx, my, 1.95], rz)

FURN = [
    {"type": "desk", "center": [L - 0.30, 1.5, 0.755], "extents": [0.60, 1.7, 0.05], "rz": 0.0, "color": "#b7b7b7"},
    {"type": "desk", "center": [L - 0.30, 0.85, 0.36], "extents": [0.55, 0.5, 0.72], "rz": 0.0, "color": "#a9a9a9"},
    {"type": "desk", "center": [L - 0.30, 2.15, 0.36], "extents": [0.55, 0.5, 0.72], "rz": 0.0, "color": "#a9a9a9"},
    {"type": "monitor", "center": [L - 0.52, 1.18, 0.99], "extents": [0.07, 0.46, 0.30], "rz": 0.0, "color": "#6f6f6f"},
    {"type": "monitor", "center": [L - 0.52, 1.18, 0.86], "extents": [0.12, 0.24, 0.14], "rz": 0.0, "color": "#8f8f8f"},
    {"type": "monitor", "center": [L - 0.52, 1.82, 0.99], "extents": [0.07, 0.46, 0.30], "rz": 0.0, "color": "#6f6f6f"},
    {"type": "monitor", "center": [L - 0.52, 1.82, 0.86], "extents": [0.12, 0.24, 0.14], "rz": 0.0, "color": "#8f8f8f"},
    {"type": "chair", "center": [1.35, 1.5, 0.45], "extents": [0.5, 0.5, 0.06], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.06, 1.5, 0.72], "extents": [0.08, 0.5, 0.55], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.35, 1.5, 0.16], "extents": [0.07, 0.07, 0.18], "rz": 0.0, "color": "#cfcfcf"},
    {"type": "chair", "center": [1.35, 1.5, 0.03], "extents": [0.4, 0.4, 0.04], "rz": 0.0, "color": "#cfcfcf"},
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


def export_desc():
    descs = []
    for p in PANELS:
        descs.append({"type": p["type"], "center": p["center"], "extents": p["extents"], "rz": p["rz"],
                      "color": "#16a2a2" if p["type"] == "panel" else "#3f9b5a"})
    for t in TRAPS:
        descs.append({"type": "trap", "center": t["center"], "extents": t["extents"], "rz": t["rz"], "color": "#f08c0a"})
    for f in FURN:
        descs.append({"type": f["type"], "center": f["center"], "extents": f["extents"], "rz": f["rz"], "color": f["color"]})
    for s in SHELL:
        descs.append({"type": "wall", "center": s["center"], "extents": s["extents"], "rz": s["rz"], "color": s["color"]})
    return descs


YUP = [[1.0, 0.0, 0.0, 0.0],
       [0.0, 0.0, 1.0, 0.0],
       [0.0, -1.0, 0.0, 0.0],
       [0.0, 0.0, 0.0, 1.0]]

scene = trimesh.Scene()
for d in export_desc():
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

print("OK:", len(PANELS), "panels,", len(TRAPS), "traps")
print("glb/obj/json exportados en", BASE)