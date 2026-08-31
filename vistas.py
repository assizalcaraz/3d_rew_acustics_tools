import os

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Arc, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from geometria import (PANELS, TRAPS, FURN, SHELL, item_corners, L, W, H)

BASE = os.path.dirname(os.path.abspath(__file__))
DPI = 160

GREY = "#4a4a4a"


def convex_hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def project(box, view):
    c = item_corners(box)
    pairs = c.T.tolist()
    if view == "xy":
        return [(p[0], p[1]) for p in pairs]
    if view == "yz":
        return [(p[1], p[2]) for p in pairs]
    if view == "xz":
        return [(p[0], p[2]) for p in pairs]


def draw_box(ax, box, view, fc, ec=None, hatch=None, alpha=0.55, lw=1.2, zorder=3):
    hull = convex_hull(project(box, view))
    p = Polygon(hull, closed=True, facecolor=fc, edgecolor=ec or fc, hatch=hatch,
                alpha=alpha, linewidth=lw, zorder=zorder)
    ax.add_patch(p)


def dim_h(ax, x1, x2, y, label, dy=0.06, fs=8.5, extra=""):
    ax.plot([x1, x2], [y, y], color=GREY, lw=1.0, zorder=6)
    for x in (x1, x2):
        ax.plot([x, x], [y - dy, y + dy], color=GREY, lw=1.0, zorder=6)
    ax.text((x1 + x2) / 2, y + dy * 1.6, label + extra, ha="center", va="bottom",
            fontsize=fs, color="#222222", zorder=6)


def dim_v(ax, y1, y2, x, label, dx=0.06, fs=8.5):
    ax.plot([x, x], [y1, y2], color=GREY, lw=1.0, zorder=6)
    for y in (y1, y2):
        ax.plot([x - dx, x + dx], [y, y], color=GREY, lw=1.0, zorder=6)
    ax.text(x + dx * 1.8, (y1 + y2) / 2, label, ha="left", va="center",
            fontsize=fs, color="#222222", zorder=6)


def header(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color="#1F2A44")
    ax.text(0.0, 1.02, sub, transform=ax.transAxes, fontsize=8, color="#666666", va="bottom")


def wall_rect(ax, x0, y0, dx, dy, fc="#e9e9e9", ec="#bbbbbb"):
    ax.add_patch(Rectangle((x0, y0), dx, dy, facecolor=fc, edgecolor=ec, lw=1.4, zorder=1))


# ---------------- PLANTA ----------------
fig, ax = plt.subplots(figsize=(9.2, 8.2))
header(ax, "PLANTA (vista superior)", "Opción B - 12 paneles 50mm + 8 trampas 100mm - cotas en metros")

wall_rect(ax, 0, 0, L, W)
for p in PANELS:
    if p["type"] == "ceil":
        draw_box(ax, p, "xy", "#3f9b5a", ec="#2e7343", hatch="//", alpha=0.35, zorder=2)
    elif p["center"][1] < 0.1:
        draw_box(ax, p, "xy", "#16a2a2", ec="#0f7878", alpha=0.8)
    elif p["center"][1] > W - 0.1:
        draw_box(ax, p, "xy", "#16a2a2", ec="#0f7878", alpha=0.8)

for t in TRAPS:
    if t["type"] == "trap":
        draw_box(ax, t, "xy", "#f08c0a", ec="#c47208", alpha=0.85)
    else:
        draw_box(ax, t, "xy", "#c9a227", ec="#9a7a1a", alpha=0.9, zorder=4)

for f in FURN:
    if f["type"] in ("desk", "chair"):
        draw_box(ax, f, "xy", "#dcdcdc", ec="#999999", alpha=0.6)

ax.add_patch(Arc((0.15, 0.0), 0.8, 0.8, angle=0, theta1=0, theta2=90,
                 color="#b58b52", lw=1.2, zorder=4))
ax.plot([0.15, 0.95], [0.0, 0.0], color="#b58b52", lw=3.0, zorder=4)
ax.plot([1.1, 2.3], [W, W], color="#74b6d4", lw=3.0, zorder=4)

dim_h(ax, 0, L, -0.18, "3,20", dy=0.055)
dim_v(ax, 0, W, L + 0.16, "3,00", dx=0.055)
dim_v(ax, W - 0.6, W, -0.16, "0,60", dx=0.05)
dim_h(ax, 0, 0.6, W + 0.14, "0,60", dy=0.05)
dim_h(ax, 1.9, 2.5, -0.42, "panel 0,60 x 1,20", dy=0.045)

ax.text(1.75, -0.62, "escritorio y monitores (solo referencia)", fontsize=8, color="#888888", ha="center")

ax.set_xlim(-0.75, 3.85)
ax.set_ylim(-0.75, 3.6)
ax.set_aspect("equal")
ax.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(BASE, "vista_planta.png"), dpi=DPI)
plt.close()

# ---------------- ALZADO FRONTAL (pared x=L detrás de monitores) ----------------
fig, ax = plt.subplots(figsize=(8.8, 9.0))
header(ax, "ALZADO FRONTAL (pared detrás de monitores, x = 3,20)", "3 paneles 0,60 x 1,20 - cota en metros")

wall_rect(ax, 0, 0, W, H)
for p in PANELS:
    if p["center"][0] > L - 0.1:
        draw_box(ax, p, "yz", "#16a2a2", ec="#0f7878", alpha=0.85)

dim_v(ax, 0, H, -0.16, "3,00", dx=0.055)
dim_h(ax, 0, W, H + 0.14, "3,00", dy=0.05)
dim_h(ax, 0.3, 0.9, 3.16, "panel 0,60", dy=0.05)
dim_v(ax, 0.6, 1.8, 3.0, "1,20", dx=0.05)
dim_v(ax, 0, 0.6, 3.0, "0,60", dx=0.05)

ax.set_xlim(-0.65, 3.55)
ax.set_ylim(-0.3, 3.5)
ax.set_aspect("equal")
ax.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(BASE, "vista_alzado_frontal.png"), dpi=DPI)
plt.close()

# ---------------- ALZADO LATERAL (pared y=W, ventana) ----------------
fig, ax = plt.subplots(figsize=(9.4, 9.0))
header(ax, "ALZADO LATERAL (pared de la ventana, y = 3,00)", "paneles laterales + paneles colgados del techo - cota en metros")

wall_rect(ax, 0, 0, L, H)
for p in PANELS:
    if p["center"][1] > W - 0.1:
        draw_box(ax, p, "xz", "#16a2a2", ec="#0f7878", alpha=0.85)
for p in PANELS:
    if p["type"] == "ceil":
        draw_box(ax, p, "xz", "#3f9b5a", ec="#2e7343", hatch="//", alpha=0.4)
for f in FURN:
    if f["type"] == "window":
        draw_box(ax, f, "xz", "#aedff0", ec="#6aa9c4", alpha=0.9)

dim_h(ax, 0, L, -0.18, "3,20", dy=0.055)
dim_v(ax, 0, H, -0.16, "3,00", dx=0.055)
dim_v(ax, 2.585, H, 3.42, "0,42 colgado\n", dx=0.05)
dim_v(ax, 0.6, 1.8, 3.42, "1,20", dx=0.05)
dim_h(ax, 1.9, 2.5, 3.16, "panel lateral 0,60", dy=0.05)

ax.set_xlim(-0.75, 3.9)
ax.set_ylim(-0.3, 3.5)
ax.set_aspect("equal")
ax.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(BASE, "vista_alzado_lateral.png"), dpi=DPI)
plt.close()

# ---------------- VISTA 3D ----------------
fig = plt.figure(figsize=(11, 9))
ax = fig.add_subplot(111, projection="3d")
ax.set_title("VISTA AXONOMÉTRICA - modelo paramétrico (medidas reales)", fontsize=13,
             fontweight="bold", color="#1F2A44", loc="left")


def draw_box_3d(ax, box, color, alpha=1.0, lw=0.4, ec="#333333"):
    if box.get("shape") == "prism":
        v = item_corners(box).T.tolist()
        faces = [
            [v[0], v[2], v[4]],
            [v[1], v[5], v[3]],
            [v[0], v[1], v[3], v[2]],
            [v[2], v[3], v[5], v[4]],
            [v[4], v[5], v[1], v[0]],
        ]
        ax.add_collection3d(Poly3DCollection(faces, facecolor=color, alpha=alpha, linewidths=lw,
                                             edgecolors=ec, zsort="max"))
        return
    c = item_corners(box).T.tolist()
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    quads = [[c[i] for i in f] for f in faces]
    ax.add_collection3d(Poly3DCollection(quads, facecolor=color, alpha=alpha, linewidths=lw,
                                         edgecolors=ec, zsort="max"))


def room_wireframe(ax):
    edges = [
        (0, 0, 0), (L, 0, 0), (L, W, 0), (0, W, 0), (0, 0, 0),
        (0, 0, H), (L, 0, H), (L, W, H), (0, W, H), (0, 0, H),
        (0, 0, 0), (0, W, 0), (L, W, 0), (L, 0, 0), (L, 0, H),
        (L, W, H), (0, W, H), (0, W, 0), (L, W, 0), (L, W, H),
    ]
    xs, ys, zs = zip(*edges)
    ax.plot(xs, ys, zs, color="#4a4a4a", lw=1.2)


room_wireframe(ax)
for f in FURN:
    draw_box_3d(ax, f, f["color"])
for p in PANELS:
    draw_box_3d(ax, p, "#16a2a2" if p["type"] == "panel" else "#3f9b5a")
for t in TRAPS:
    draw_box_3d(ax, t, "#f08c0a" if t["type"] == "trap" else "#c9a227")

ax.set_box_aspect((L, W, H))
ax.set_xlim(0, L); ax.set_ylim(0, W); ax.set_zlim(0, H)
ax.set_xlabel("x (3,20)"); ax.set_ylabel("y (3,00)"); ax.set_zlabel("z (3,00)")
ax.view_init(elev=18, azim=-55)
plt.tight_layout()
plt.savefig(os.path.join(BASE, "vista_3d.png"), dpi=DPI)
plt.close()

print("vistas generadas en", BASE)