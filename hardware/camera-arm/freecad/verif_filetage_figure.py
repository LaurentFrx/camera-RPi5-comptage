# -*- coding: utf-8 -*-
"""verif_filetage_figure.py — figure de vérification du filetage à partir des coupes exportées par verif_filetage_freecad.py.
Usage : python3 verif_filetage_figure.py <coupes_filet.json> <dossier_renders>"""
import json, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
d = json.load(open(sys.argv[1])); P = d["P"]
fig, axes = plt.subplots(1, 3, figsize=(15, 6), dpi=130)
for ax, key, titre in zip(axes, ("vis", "ecrou_hex", "ecrou_rosette"), ("Vis moletée M8 pas 2, L11 — coupe axiale (plan y = 0)", "Écrou hexagonal 13 × 5 — coupe axiale", "Écrou-rosette — coupe axiale")):
    for poly in d[key]:
        xs = [p[0] for p in poly]; zs = [p[1] for p in poly]
        ax.plot(xs, zs, color="#c94a4a", lw=1.2)
    ax.set_aspect("equal"); ax.grid(True, lw=0.3, alpha=0.5); ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
    ax.set_title(titre, fontsize=10)
# profil théorique et jeu sur la vis
ax = axes[0]
r_maj = P["vis_dmaj"] / 2; r_root = r_maj - P["vis_prof"]
ax.axvline(r_maj, color="#25558a", ls="--", lw=0.8); ax.axvline(r_root, color="#25558a", ls="--", lw=0.8)
ax.axvline(-r_maj, color="#25558a", ls="--", lw=0.8); ax.axvline(-r_root, color="#25558a", ls="--", lw=0.8)
ax.text(r_maj + 0.2, P["vis_tete_h"] + 2, f"Ø{P['vis_dmaj']:g} (crête)", color="#25558a", fontsize=8)
ax.text(r_root - 3.2, P["vis_tete_h"] + 2, f"Ø{2*r_root:g} (fond)", color="#25558a", fontsize=8)
ax.text(0, -1.2, f"pas {P['vis_pas']:g} mm · profondeur {P['vis_prof']:g} · crête plate {P['vis_crete']:g} · jeu radial écrou {P['vis_jeu']:g}", ha="center", fontsize=8.5)
ax = axes[1]
rt = r_maj + P["vis_jeu"]; rr = rt - P["vis_prof"]
for r in (rt, rr, -rt, -rr):
    ax.axvline(r, color="#25558a", ls="--", lw=0.8)
ax.text(rr - 0.1, P["hexnut_h"] + 0.3, f"trou : Ø{2*rr:.1f} / Ø{2*rt:.1f}", color="#25558a", fontsize=8, ha="right")
fig.suptitle("Vérification du filetage imprimé (généré par loft de sections, sans balayage hélicoïdal) — la coupe montre les dents de la vis et les gorges des écrous", fontsize=11)
fig.savefig(sys.argv[2] + "/43_verification_filetage.png", bbox_inches="tight")
print("figure OK")
