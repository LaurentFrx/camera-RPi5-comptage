# -*- coding: utf-8 -*-
"""
make_renders.py — génère la série de rendus PNG de l'étude à partir des STL exportés par bras_camera_cm3.py.

Usage : python3 make_renders.py <dossier_export> <dossier_renders>
"""
import os, sys, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_stl import render

EXP, OUTD = sys.argv[1], sys.argv[2]
os.makedirs(OUTD, exist_ok=True)
A = os.path.join(EXP, "stl_assemblage")
C = os.path.join(EXP, "stl_conception")
S = os.path.join(EXP, "stl")

COL = {
    "pied": [0.55, 0.58, 0.62], "bague": [0.80, 0.60, 0.25], "collier": [0.25, 0.55, 0.85],
    "bras_corps": [0.88, 0.50, 0.15], "fourche_epaule": [0.93, 0.66, 0.22], "fourche_tete": [0.93, 0.66, 0.22],
    "tete_coque": [0.30, 0.68, 0.42], "tete_facade": [0.50, 0.82, 0.58], "cm3": [0.12, 0.42, 0.18],
    "vis": [0.85, 0.22, 0.22], "ecrou": [0.75, 0.18, 0.18], "goupille": [0.45, 0.45, 0.48],
}

def color_of(name):
    for k, v in COL.items():
        if name.startswith(k):
            return v
    return [0.6, 0.6, 0.6]

def T(dx=0, dy=0, dz=0):
    m = np.eye(4); m[:3, 3] = [dx, dy, dz]; return m.tolist()

def parts_from_dir(d, names=None, exclude=(), offsets=None):
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".stl"):
            continue
        n = f[:-4]
        if names is not None and n not in names:
            continue
        if any(n.startswith(e) for e in exclude):
            continue
        p = {"file": os.path.join(d, f), "color": color_of(n)}
        if offsets and n in offsets:
            p["transform"] = offsets[n]
        out.append(p)
    return out

def go(name, scene):
    scene.setdefault("width", 1600); scene.setdefault("height", 1100)
    out = os.path.join(OUTD, name + ".png")
    render(scene, out); print("→", out)

# ---- 1. assemblage, pose par défaut (épaule 60°, tête 120° : visée horizontale) ----------------
go("01_assemblage_iso", {"view": "iso", "parts": parts_from_dir(A), "scale_bar_mm": 50,
    "title": "Assemblage — pose par défaut : lacet 0°, épaule 60°, tête 120° (visée horizontale)",
    "subtitle": "gris : pied · bleu : collier-tourelle · orange : bras (corps + 2 fourches) · vert : tête caméra · rouge : visserie imprimée"})
go("02_assemblage_face", {"view": "front", "parts": parts_from_dir(A), "scale_bar_mm": 50,
    "title": "Assemblage — vue de face (plan vertical du bras)"})
go("03_assemblage_dessus", {"view": "top", "parts": parts_from_dir(A), "scale_bar_mm": 50,
    "title": "Assemblage — vue de dessus"})
go("04_assemblage_cote", {"view": [0, 0], "parts": parts_from_dir(A), "scale_bar_mm": 50,
    "title": "Assemblage — vue de côté (depuis +X, face à l'objectif)"})

# ---- 2. autres poses ------------------------------------------------------------------------
for pose, titre in (("repos", "Pose « repos » : bras vertical, tête dans le prolongement (encombrement minimal)"),
                    ("horizontal", "Pose « horizontal » : épaule 90°, tête 90° → visée horizontale, bras à 28 mm au-dessus de la platine"),
                    ("lacet45", "Pose « lacet 45° » : la tourelle tourne l'ensemble du bras autour du fût"),
                    ("plongee", "Pose « plongée » : épaule 90°, tête 150° → visée à -60° (limite : rayon nappe 4,6 mm)")):
    d = os.path.join(A, "pose_" + pose)
    go("05_pose_" + pose, {"view": "iso", "parts": parts_from_dir(d), "scale_bar_mm": 50, "title": titre})

# ---- 3. détails : articulation d'épaule éclatée le long de l'axe Y ---------------------------------
off = {"vis_epaule": T(0, 34, 0), "ecrou_epaule": T(0, 14, 0), "vis_epaule_B": T(0, -34, 0), "ecrou_epaule_B": T(0, -14, 0)}
go("06_detail_epaule_eclate", {"view": [40, 24], "scale_bar_mm": 20,
    "parts": parts_from_dir(A, names=["collier", "fourche_epaule", "vis_epaule", "ecrou_epaule", "vis_epaule_B", "ecrou_epaule_B", "bague", "pied", "bras_corps"], offsets=off),
    "title": "Articulation d'épaule éclatée suivant l'axe : vis → oreille crantée → écrou-rosette → noix, des deux côtés",
    "subtitle": "charnière symétrique : un écrou-rosette (hexagone 13) prisonnier de chaque plaque de noix, 24 dents (pas 15°) emboîtées dans chaque oreille, une vis par côté"})
off2 = {"vis_tete": T(0, 34, 0), "ecrou_tete": T(0, 14, 0), "vis_tete_B": T(0, -34, 0), "ecrou_tete_B": T(0, -14, 0)}
go("07_detail_tete_eclate", {"view": [40, 24], "scale_bar_mm": 20,
    "parts": parts_from_dir(A, names=["tete_coque", "tete_facade", "cm3", "fourche_tete", "vis_tete", "ecrou_tete", "vis_tete_B", "ecrou_tete_B"], offsets=off2),
    "title": "Articulation de tête éclatée suivant l'axe (deux vis, deux écrous-rosette) et boîtier caméra fermé"})

# ---- 4. tête caméra éclatée (repère de conception : z = profondeur, avant = +z) --------------------
go("08_tete_eclatee", {"view": [-55, 28], "scale_bar_mm": 10,
    "parts": [{"file": os.path.join(C, "05_tete_coque.stl"), "color": COL["tete_coque"]},
              {"file": os.path.join(C, "90_maquette_cm3.stl"), "color": COL["cm3"], "transform": T(0, 0, 14)},
              {"file": os.path.join(C, "06_tete_facade.stl"), "color": COL["tete_facade"], "transform": T(0, 0, 30)}],
    "title": "Tête caméra éclatée : coque arrière (noix de charnière, plots + pions Ø1,8) · Camera Module 3 · façade encliquetable",
    "subtitle": "PCB plaqué sur les 4 plots de la coque par les 4 fûts de la façade, portés par des languettes-ressorts (précontrainte 0,2 mm) : zéro vis M2, zéro jeu"})
go("09_tete_coque_interieur", {"view": [-60, 55], "scale_bar_mm": 10,
    "parts": [{"file": os.path.join(C, "05_tete_coque.stl"), "color": COL["tete_coque"]}],
    "title": "Coque arrière : logement PCB, épaulement de jupe, rainures d'encliquetage, fente nappe 18 × 2,4 évasée, noix symétrique"})
go("10_tete_facade_interieur", {"view": [-60, -50], "scale_bar_mm": 10,
    "parts": [{"file": os.path.join(C, "06_tete_facade.stl"), "color": COL["tete_facade"]}],
    "title": "Façade vue de l'intérieur : jupe 1,2 + 2 crochets, 4 fûts d'appui sur languettes-ressorts, ouverture optique 14 (r 3)"})
go("11_tete_facade_face", {"view": "top", "scale_bar_mm": 10,
    "parts": [{"file": os.path.join(C, "06_tete_facade.stl"), "color": COL["tete_facade"]}],
    "title": "Façade de face : ouverture 14 chanfreinée 0,6 à 45°, 4 languettes-ressorts (fentes 0,6 en U) portant les fûts d'appui",
    "subtitle": "languettes hautes : le long de x, encastrées vers le centre (8,5 mm utiles) ; basses : le long de y, encastrées vers la paroi basse (7,9 mm)"})

# ---- 5. pièces seules, orientation d'impression (plateau = z = 0) -------------------------------
pieces = [
    ("01_pied_couvercle", "Pied pour couvercle : platine 50×46 décalée (bord affleurant la paroi), 4 fentes 3,4×8, fût creux Ø26/Ø20 — imprimé tel quel"),
    ("01c_gabarit_percage_couvercle", "Gabarit de perçage du couvercle (plaque 1,2 mm) : trou nappe Ø22 + 4 trous Ø3,4 — à poser sur le couvercle"),
    ("01a_pied_plat_centre", "Variante : platine 46×46 centrée sur le fût"),
    ("01b_cavalier_adaptateur", "Variante : adaptateur cavalier — imprimé retourné, joues vers le haut"),
    ("02_bague_retenue", "Bague de retenue Ø32/Ø24,1 × 3 — emmanchée (ou collée) sur le tenon"),
    ("03_collier_tourelle", "Collier-tourelle : anneau fendu Ø34/Ø26,3 × 12, pattes de serrage, noix d'épaule — imprimé debout"),
    ("04a_bras_corps_L150", "Corps de bras 124 × 24 × 8 (entraxe 150), canal 18 × 2,4 traversant — imprimé à plat (pont de 18 mm)"),
    ("04a_bras_corps_L170_alt", "Corps de bras alternatif 144 × 24 × 8 (entraxe 170) — si la mesure de nappe le permet"),
    ("04b_fourche_x2", "Fourche (×2) — imprimée debout sur le manchon : oreilles verticales crantées des deux côtés, entonnoir de canal"),
    ("05_tete_coque", "Coque de tête — imprimée sur sa paroi haute, noix (symétrique) vers le haut"),
    ("06_tete_facade", "Façade — imprimée face avant sur le plateau (fentes de ressort verticales)"),
    ("07_vis_M8_L11_x4", "Vis moletée M8 pas 2 L11 (×4) — tête sur le plateau, filet vertical"),
    ("08_vis_M8_L20", "Vis moletée M8 pas 2 L20 (collier)"),
    ("09_ecrou_rosette_x4", "Écrou-rosette (×4) — hexagone 3,5 sur le plateau, cône 45°, dents vers le haut"),
    ("10_ecrou_hex", "Écrou hexagonal 13 × 5"),
    ("04c_goupille_x4", "Goupille Ø3 × 7 à tête (×4, facultative)"),
]
for n, titre in pieces:
    f = os.path.join(S, n + ".stl")
    if os.path.exists(f):
        go("20_piece_" + n, {"view": "iso", "parts": [{"file": f, "color": color_of(n.split("_", 1)[1] if "_" in n else n)
                                                          if False else [0.80, 0.80, 0.82]}],
                              "scale_bar_mm": 20 if n.startswith(("07", "08", "09", "10", "04c", "02")) else 50,
                              "title": titre, "width": 1300, "height": 900})

# ---- 6. planche « toutes les pièces à imprimer » (disposition plateau) --------------------------
plate = []
x = 0.0; row_y = 0.0; row_h = 0.0; col_w = 0
from render_stl import load_stl
for n, _ in pieces:
    f = os.path.join(S, n + ".stl")
    if not os.path.exists(f) or n in ("01a_pied_plat_centre", "01b_cavalier_adaptateur", "04a_bras_corps_L170_alt"):
        continue
    V = load_stl(f); bb = V.reshape(-1, 3)
    w, h = bb[:, 0].max() - bb[:, 0].min(), bb[:, 1].max() - bb[:, 1].min()
    if x + w > 250:
        x = 0.0; row_y += row_h + 12; row_h = 0
    plate.append({"file": f, "color": [0.80, 0.80, 0.82], "transform": T(x - bb[:, 0].min(), row_y - bb[:, 1].min(), 0)})
    x += w + 12; row_h = max(row_h, h)
go("30_planche_impression", {"view": [-70, 40], "parts": plate, "scale_bar_mm": 50, "width": 1800, "height": 1100,
    "title": "Kit à imprimer (orientation d'impression) : pied couvercle, gabarit, bague, collier, corps L150, 2 fourches, coque, façade, 2 vis L11, vis L20, 2 écrous-rosette, écrou hex, 4 goupilles"})
print("terminé")
