# -*- coding: utf-8 -*-
"""schemas_2d.py — schémas cotés (matplotlib) : coupe de l'articulation et trajet de la nappe.
Usage : python3 schemas_2d.py <dossier_renders>"""
import sys, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch, Arc

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans"})


def dim(ax, x0, x1, y, text, above=True, color="#333"):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=color, lw=1.1))
    ax.text((x0 + x1) / 2, y + (0.5 if above else -1.4), text, ha="center", va="bottom", color=color, fontsize=10)


def vdim(ax, x, y0, y1, text, color="#333", dx=0.6):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=color, lw=1.1))
    ax.text(x + dx, (y0 + y1) / 2, text, ha="left", va="center", color=color, fontsize=10)


# =====================================================================================================
# 1. COUPE DE L'ARTICULATION (plan Y-Z passant par l'axe ; Y = axe de charnière, Z = plan de nappe)
# =====================================================================================================
fig, ax = plt.subplots(figsize=(14, 8.5), dpi=130)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Coupe de l'articulation « à fenêtre » (plan Y–Z par l'axe) — cotes en mm", fontsize=13, pad=12)

c_noix, c_fourche, c_ecrou, c_vis, c_nappe = "#59b26e", "#e8a53a", "#c94a4a", "#c94a4a", "#d98b2b"
# plaques de noix : |Y| ∈ [9, 15], disque R10 (ici rectangle Z ±10)
for s in (+1, -1):
    y0 = min(s * 9, s * 15)
    ax.add_patch(Rectangle((y0, -10), 6, 20, fc=c_noix, ec="k", lw=1))
# col vers l'hôte (en bas du schéma, Z < -10 : représenté par un hachurage court)
for s in (+1, -1):
    y0 = min(s * 9, s * 15)
    ax.add_patch(Rectangle((y0, -16), 6, 6, fc=c_noix, ec="k", lw=1, hatch="//", alpha=0.6))
ax.text(0, -14.5, "vers le corps hôte\n(collier ou coque)", ha="center", va="center", fontsize=9, color="#2a6b3d")
# charnière symétrique : de chaque côté (s = ±1), poche hexagonale |Y| ∈ [10, 15.5] + écrou-rosette (corps hex 3,5 : |Y| ∈ [11.5, 15],
# cône 15→17.35, plat →18, dents 18→19), oreille crantée |Y| ∈ [19, 23] (alésage Ø8,6), vis moletée (tête |Y| ∈ [23, 28], filet jusqu'à |Y| = 12)
for s in (+1, -1):
    def R(y0, w, z0, h, **kw):
        ax.add_patch(Rectangle((min(s * y0, s * (y0 + w)), z0), w, h, **kw))
    R(10, 5.5, -6.65, 13.3, fc="white", ec="k", lw=0.8, ls="--")                        # poche (profonde 5 + 0,5)
    R(11.5, 3.5, -6.5, 13.0, fc=c_ecrou, ec="k", lw=1)                                   # corps hex 3,5 (13 sur plats)
    ax.add_patch(Polygon([(s * 15, -7.65), (s * 17.35, -10), (s * 17.35, 10), (s * 15, 7.65)], closed=True, fc=c_ecrou, ec="k", lw=1))  # cône 45°
    R(17.35, 0.65, -10, 20, fc=c_ecrou, ec="k", lw=1)                                    # plat
    for zc in (-8.25, 8.25):                                                             # dents |Y| ∈ [18, 19], r ∈ [6.5, 10]
        for k in range(-2, 3):
            z = zc + k * 0.7
            ax.add_patch(Polygon([(s * 18, z - 0.35), (s * 19, z), (s * 18, z + 0.35)], closed=True, fc=c_ecrou, ec="k", lw=0.5))
    R(19, 4, -11, 22, fc=c_fourche, ec="k", lw=1)                                        # oreille crantée
    R(19, 4, -4.3, 8.6, fc="white", ec="k", lw=0.8)                                      # alésage Ø8,6
    R(23, 5, -9, 18, fc=c_vis, ec="k", lw=1)                                             # tête de vis Ø18 × 5
    R(12, 11, -3.9, 7.8, fc=c_vis, ec="k", lw=1, hatch="||", alpha=0.9)                  # filet Ø7,8 L11
    ax.text(s * 25.5, 0, "M8\npas 2", ha="center", va="center", fontsize=8, color="white")
# enfoncement de montage : l'écrou peut reculer de 1,5 mm au fond de sa poche (dents à |Y| = 17,5 < 18) → la fourche se glisse sur la noix
ax.annotate("", (10, 8.2), (11.5, 8.2), arrowprops=dict(arrowstyle="<->", color="#c94a4a", lw=1))
ax.text(10.75, 8.9, "1,5", ha="center", fontsize=8, color="#c94a4a")
# nappe : 16 large, dans le plan Z = 0, entre les plaques (|Y| < 9)
ax.add_patch(Rectangle((-8, -0.15), 16, 0.3, fc=c_nappe, ec="none"))
ax.text(0, 1.2, "nappe 16 mm (plan Z = 0)", ha="center", fontsize=9, color="#8a5a10")
# axe
ax.plot([-26, 30], [0, 0], color="#555", lw=0.8, ls="-.")
ax.text(29.5, -12.2, "axe de charnière (Y)", va="top", ha="right", fontsize=9, color="#555")
# cotes
dim(ax, -9, 9, 12.5, "fenêtre 18 (canal 18 × 2,4)")
dim(ax, 9, 15, 12.5, "6")
dim(ax, 15, 19, 12.5, "4")
dim(ax, 19, 23, 12.5, "4")
dim(ax, -15, -9, 12.5, "6")
dim(ax, -19, -15, 12.5, "4")
dim(ax, -23, -19, 12.5, "4")
dim(ax, -23, 23, 16.5, "fourche 46 hors tout")
vdim(ax, -31.5, -10, 10, "noix\nR 10", dx=-4.5)
vdim(ax, 33, -11, 11, "oreille\nR 11")
# légende
leg = [("plaques de noix (coque / collier)", c_noix), ("oreilles de fourche (bras), crantées", c_fourche),
       ("écrous-rosette + vis moletées (imprimés, 2 par axe)", c_ecrou), ("nappe caméra", c_nappe)]
for i, (t, c) in enumerate(leg):
    ax.add_patch(Rectangle((-26, -22 + i * 2.2), 2, 1.6, fc=c, ec="k", lw=0.6))
    ax.text(-23.3, -21.2 + i * 2.2, t, va="center", fontsize=9.5)
ax.text(4, -21.5, "Serrage symétrique : chaque vis tire son écrou-rosette contre son oreille ;\n"
                  "les 24 dents (pas 15°) verrouillent l'angle des deux côtés, l'hexagone\n"
                  "bloque l'écrou dans la noix. Montage : écrous enfoncés au fond des poches,\n"
                  "fourche glissée sur la noix, deux vis. Desserrer ½ tour → régler → resserrer.",
        fontsize=9.5, va="center", bbox=dict(fc="#f6f6f6", ec="#bbb"))
ax.set_xlim(-34, 40); ax.set_ylim(-25, 19)
fig.savefig(os.path.join(OUT, "40_schema_coupe_articulation.png"), bbox_inches="tight")
plt.close(fig)

# =====================================================================================================
# 2. TRAJET DE LA NAPPE DANS LA FENÊTRE (plan X-Z), pour 0°, 90°, 120° de pliage
# =====================================================================================================
f = 11.0
fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), dpi=130)
for ax, beta in zip(axes, (0, 90, 120)):
    ax.set_aspect("equal"); ax.axis("off")
    b = math.radians(beta)
    # bras : canal fermé jusqu'à X = -f (Z ±4), oreille R11 (contour)
    ax.add_patch(Rectangle((-40, -4), 40 - f, 8, fc="#e8a53a", ec="k", lw=1, alpha=0.9))
    ax.add_patch(Rectangle((-40, -1.2), 40 - f, 2.4, fc="white", ec="none"))
    ax.add_patch(Circle((0, 0), 11, fc="none", ec="#e8a53a", lw=2, ls="--"))
    # hôte (tête/collier) : canal à partir de X = +f, tourné de beta
    def R(p):
        x, z = p
        return (x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b))
    host = [(f, -4), (40, -4), (40, 4), (f, 4)]
    ax.add_patch(Polygon([R(p) for p in host], closed=True, fc="#59b26e", ec="k", lw=1, alpha=0.9))
    ax.add_patch(Polygon([R(p) for p in [(f, -1.2), (40, -1.2), (40, 1.2), (f, 1.2)]], closed=True, fc="white", ec="none"))
    ax.add_patch(Circle((0, 0), 10, fc="none", ec="#59b26e", lw=2, ls=":"))
    # nappe : segment droit dans le bras, arc tangent dans la fenêtre, segment droit dans l'hôte
    ax.plot([-40, -f], [0, 0], color="#d98b2b", lw=3)
    e = R((f, 0)); d = R((1, 0))
    ax.plot([e[0], e[0] + 30 * d[0]], [e[1], e[1] + 30 * d[1]], color="#d98b2b", lw=3)
    if beta == 0:
        ax.plot([-f, f], [0, 0], color="#d98b2b", lw=3)
        r_txt = "nappe rectiligne (22 mm libres)"
    else:
        corde = f * math.sqrt(2 + 2 * math.cos(b)); r = corde / (2 * math.sin(b / 2))
        # centre de l'arc : à distance r de (-f,0) perpendiculairement à la tangente (+X) → (-f, -r)
        cx, cz = -f, -r
        ang = [math.degrees(math.atan2(0 - cz, -f - cx)), math.degrees(math.atan2(e[1] - cz, e[0] - cx))]
        ax.add_patch(Arc((cx, cz), 2 * r, 2 * r, angle=0, theta1=min(ang), theta2=max(ang), color="#d98b2b", lw=3))
        ax.plot([cx], [cz], "+", color="#8a5a10")
        ax.annotate("", (cx, cz), (-f, 0), arrowprops=dict(arrowstyle="<->", color="#8a5a10", lw=1))
        ax.text(cx - 1, (cz) / 2, f"r = {r:.1f}", color="#8a5a10", ha="right", fontsize=10)
        r_txt = f"rayon de pliage {r:.1f} mm"
    ax.plot([0], [0], "k+", ms=10)
    ax.set_title(f"pliage {beta}° — {r_txt}", fontsize=11)
    ax.set_xlim(-42, 42); ax.set_ylim(-42, 28)
fig.suptitle("Trajet de la nappe à travers la fenêtre : l'axe est dans le plan de la nappe → longueur quasi constante, "
             "pliage symétrique possible des deux côtés", fontsize=12)
fig.savefig(os.path.join(OUT, "41_schema_trajet_nappe.png"), bbox_inches="tight")
plt.close(fig)

# =====================================================================================================
# 3. BUDGET CÂBLE 300 mm
# =====================================================================================================
fig, ax = plt.subplots(figsize=(13, 4.4), dpi=130)
segs = [("Pi 5 → sortie boîtier\n(estimé 60)", 60, "#9aa5b1"), ("boîtier → platine\n(estimé 20)", 20, "#9aa5b1"),
        ("platine → axe épaule\n32", 32, "#25558a"), ("bras L = 150", 150, "#e8a53a"), ("axe tête → connecteur\n25,4", 25.4, "#59b26e"),
        ("courbures 6", 6, "#d98b2b")]
x = 0; k = 0
for t, w, c in segs:
    ax.barh(0, w, left=x, color=c, ec="k", height=0.6)
    if w >= 30:
        ax.text(x + w / 2, 0, t, ha="center", va="center", fontsize=9, color="white" if c in ("#25558a", "#59b26e") else "black")
    else:
        yl = 0.62 + 0.28 * (k % 3); k += 1
        ax.annotate(t.replace("\n", " "), (x + w / 2, 0.3), (x + w / 2, yl), ha="center", va="bottom", fontsize=8.5,
                    arrowprops=dict(arrowstyle="-", color="#555", lw=0.8))
    x += w
ax.barh(0, 300 - x, left=x, color="#eeeeee", ec="k", height=0.6, hatch="//")
ax.annotate(f"marge {300 - x:.1f} mm", (x + (300 - x) / 2, -0.3), (x + (300 - x) / 2, -0.75), ha="center", va="top", fontsize=9,
            arrowprops=dict(arrowstyle="-", color="#555", lw=0.8))
ax.axvline(300, color="red", lw=2); ax.text(302, -0.5, "câble 300 mm", color="red", fontsize=10)
ax.set_xlim(0, 335); ax.set_ylim(-1.05, 1.6); ax.set_yticks([]); ax.set_xlabel("mm")
ax.set_title("Budget de longueur de la nappe Standard–Mini 300 mm (entraxe de bras 150 mm) — les deux premiers tronçons sont à mesurer sur le boîtier réel", fontsize=11)
fig.savefig(os.path.join(OUT, "42_budget_nappe.png"), bbox_inches="tight")
plt.close(fig)
print("schémas OK")
