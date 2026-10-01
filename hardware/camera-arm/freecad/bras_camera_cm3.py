# -*- coding: utf-8 -*-
"""
bras_camera_cm3.py — Bras articulé 3 axes + boîtier Camera Module 3, fixé sur le boîtier du RPi 5.

Macro FreeCAD paramétrique (module Part, API Python). Tout est régénéré à partir du dictionnaire P.
Exécution :
  * headless : OUT_DIR=/chemin/sortie freecadcmd -c "exec(open('bras_camera_cm3.py').read())"
  * dans FreeCAD : Macro > Macros… > Exécuter (les documents s'ouvrent, les exports vont dans OUT_DIR
    ou, à défaut, dans ~/bras_camera_out).

Révision du 01/10 (vérification nappe / tenue de la caméra) : charnière symétrique (écrou-rosette + vis des deux côtés,
plus de tourillon : la fourche se glisse sur la noix sans écarter les oreilles), PCB plaqué sans jeu sur les plots de la
coque par 4 fûts de façade portés par des languettes-ressorts découpées dans la plaque avant (précontrainte 0,2 mm),
entonnoirs à toutes les entrées de canal, ouverture optique 14 chanfreinée, dégagement objectif 1,5, corps de bras
ajusté serré dans les fourches.

Conventions :
  * unités mm, Z vers le haut pour le pied ; repère « bras » : X = longueur, Y = axe des charnières,
    Z = épaisseur (plan de la nappe en Z = 0, axe d'articulation décalé de P['excentr'] vers +Z).
  * repère « tête » : x = largeur PCB, y = hauteur PCB (connecteur en bas), z = profondeur (avant = +z).
"""
import os, sys, math, json, time

import FreeCAD as App
import Part
from FreeCAD import Vector as V, Placement, Rotation as Rot

T0 = time.time()
OUT = os.environ.get("OUT_DIR") or os.path.join(os.path.expanduser("~"), "bras_camera_out")
for sub in ("fcstd", "step", "stl", "stl_conception", "stl_assemblage"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

# =============================================================================================
# 1. PARAMÈTRES
# =============================================================================================
P = dict(
    # --- nappe (Raspberry Pi Camera Cable Standard–Mini 300 mm) ------------------------------
    nappe_l=16.0, nappe_ep=0.3, canal_l=18.0, canal_h=2.4,
    chanf_canal=0.6, chanf_fenetre=1.5, chanf_fente=0.8, chanf_fut=1.2,   # entonnoirs d'entrée (corps, bouche de fourche, fente de tête, alésage du fût)
    # --- bras -------------------------------------------------------------------------------
    bras_L=float(os.environ.get("ARM_L", 150.0)),  # entraxe épaule → tête
    bras_l=24.0, bras_h=8.0,
    # --- articulation « fenêtre » commune (épaule et tête) -------------------------------------
    excentr=0.0,          # axe de charnière DANS le plan de nappe (trajet de nappe constant, pliage symétrique)
    fen_demi=11.0,        # nappe libre de chaque côté de l'axe = rayon des oreilles (rayon de pliage ≥ 6 mm jusqu'à 120°)
    noix_R=10.0, noix_ep=6.0, noix_gap=18.0, noix_col=12.0, noix_col_epaule=16.0,   # plaques de noix ; col plus haut à l'épaule (dégagement bague)
    oreille_ep=4.0, oreille_R=11.0, oreille_trou=8.6,        # oreilles de fourche (côté bras)
    manchon_L=21.0, manchon_ep=2.8, manchon_jeu=0.1, goupille_d=3.2,  # emmanchement corps de bras → fourche (serré : à coller)
    jeu_AB=4.0,           # écart face de noix → face d'oreille, comblé par la flasque + dents de l'écrou-rosette (2 côtés)
    dents_n=24, dents_h=1.0, dents_r1=6.5, dents_r2=10.0,
    ecrou_hex=13.0, ecrou_corps=3.5, ecrou_poche=5.0, ecrou_jeu=0.3, ecrou_flasque_r=10.0,   # hexagone 3,5 dans une poche de 5 : l'écrou s'enfonce de 1,5 pour glisser la fourche
    # --- visserie imprimée M8 « pas gros » 2 mm --------------------------------------------
    vis_dmaj=7.8, vis_pas=2.0, vis_prof=0.9, vis_jeu=0.3, vis_tete_d=18.0, vis_tete_h=5.0,
    vis_crete=0.35, vis_fond=0.5, filet_sections_par_pas=12, filet_points=48, vis_pointe=1.2,   # construction du filet par loft de sections
    vis_L_art=11.0, vis_L_collier=20.0, hexnut_h=5.0,
    # --- tête : Raspberry Pi Camera Module 3 (standard) -----------------------------------
    pcb_l=25.0, pcb_h=23.862, pcb_ep=1.0, pcb_jeu_l=0.6, pcb_jeu_h=0.5,
    trou_d=2.2, trous_dx=21.0, trous_dy=12.5, trou_bord_haut=2.0,
    objectif_c=11.5, objectif_h=8.5, ouverture=14.0, ouverture_r=3.0, ouverture_chanfrein=0.6,   # bloc objectif ≈ 11,5 mesuré sur photo ; ouverture chanfreinée à 45° côté avant
    connecteur_l=20.5, connecteur_p=5.5, connecteur_h=3.0, nappe_z_conn=1.2,
    paroi=3.0, fond=2.0, jeu_dos=4.0, facade_ep=1.5, jeu_objectif=1.5, rebord=2.0,
    plot_d=3.6, pion_d=1.8, pion_h=0.8,                                 # pions 0,2 sous la face avant du PCB : les fûts de façade portent sur le PCB, jamais sur les pions
    pcb_serrage=0.2,                                                   # les fûts de façade dépassent de 0,2 : précontrainte prise par les languettes
    ressort_l=3.0, ressort_fente=0.6, ressort_x0=2.0, ressort_x1=12.0, ressort_y0=-10.5, ressort_y1=0.5,   # languettes-ressorts de la plaque avant (fûts hauts : le long de x ; fûts bas : le long de y)
    jupe_ep=1.2, jupe_h=6.0, jupe_jeu=0.15, crochet=0.6, crochet_L=8.0,
    # --- pied, fût creux, collier-tourelle ----------------------------------------------------
    pied_c=46.0, pied_ep=4.0, fente_l=3.4, fente_L=8.0, fente_pos=17.0,
    pied_cx=50.0, pied_cy=46.0, pied_decal=7.0, fente_x=19.0, fente_y_av=-8.0, fente_y_ar=22.0,    # pied « couvercle » : bord de platine à 16 mm de l'axe du fût (= rayon du congé), fentes à 4 mm des bords
    couvercle_trou=22.0, gabarit_ep=1.2, bras_L_alt=170.0,
    fut_d=26.0, fut_alesage=20.0, fut_h=12.5, tenon_d=24.0, tenon_h=3.0, bague_d=32.0, bague_jeu=0.1,
    collier_d=34.0, collier_jeu=0.3, collier_h=12.0, fente_collier=2.0,
    patte_L=9.0, patte_l=8.0, patte_h=10.0,
    mur_ep=3.0, cavalier_h=25.0, cavalier_ep=4.0, cavalier_int_h=14.0,   # adaptateur « cavalier » (paroi verticale)
    # --- pose d'assemblage par défaut ---------------------------------------------------------
    pose_lacet=0.0, pose_epaule=60.0, pose_tete=120.0,
    # --- budget câble ------------------------------------------------------------------------
    cable_L=300.0, cable_boitier=45.0, cable_boitier_pied=0.0,   # mesuré sur photo : connecteur CAM ≈ 35 mm sous le bord ; platine posée sur le couvercle
)

# grandeurs dérivées
E = P["excentr"]
Y_A = P["noix_gap"] / 2 + P["noix_ep"] + P["jeu_AB"]          # face intérieure des oreilles (|Y|) = 19
OREILLE_OUT = Y_A + P["oreille_ep"]                             # = 23 → fourche large 46
FOURCHE_L = 2 * OREILLE_OUT
TROU_X = P["trous_dx"] / 2
TROU_Y_HAUT = P["pcb_h"] / 2 - P["trou_bord_haut"]
TROU_Y_BAS = TROU_Y_HAUT - P["trous_dy"]
OBJ_C = V(0, TROU_Y_BAS, 0)                                     # centre optique (au niveau des trous bas)
POCHE_L = P["pcb_l"] + P["pcb_jeu_l"]
POCHE_H = P["pcb_h"] + P["pcb_jeu_h"]
TETE_L = POCHE_L + 2 * P["paroi"]                               # 31.6
TETE_H = POCHE_H + 2 * P["paroi"]                               # 30.36
Z_PCB_DOS = P["fond"] + P["jeu_dos"]                            # 6.0  face arrière du PCB
Z_PCB_AV = Z_PCB_DOS + P["pcb_ep"]                              # 7.0
Z_NAPPE_TETE = Z_PCB_DOS - P["nappe_z_conn"]                    # 4.8  plan de la nappe dans la tête
Z_COQUE = Z_PCB_AV + P["rebord"]                                # 9.0  haut de la coque
Z_FACADE_INT = Z_PCB_AV + P["objectif_h"] + P["jeu_objectif"]   # 15.5
TETE_P = Z_FACADE_INT + P["facade_ep"]                          # 17.0 profondeur totale
Y_AXE_TETE = -(TETE_H / 2 + P["noix_col"])                      # -27.18
Z_AXE_TETE = Z_NAPPE_TETE + E                                   # 11.8
Z_AXE_EPAULE = P["collier_h"] + P["noix_col_epaule"]            # 28
X_AXE_EPAULE = 0.0                                              # axe d'épaule à l'aplomb du fût
FIL_R = P["vis_dmaj"] / 2

RAPPORT = {"parametres": P, "derives": dict(Y_A=Y_A, FOURCHE_L=FOURCHE_L, TETE_L=TETE_L, TETE_H=TETE_H,
                                             TETE_P=TETE_P, Z_AXE_EPAULE=Z_AXE_EPAULE, Y_AXE_TETE=Y_AXE_TETE,
                                             Z_AXE_TETE=Z_AXE_TETE), "pieces": {}, "verifications": {}}

def log(*a):
    print("[bras]", *a); sys.stdout.flush()

# =============================================================================================
# 2. PRIMITIVES
# =============================================================================================
def box(dx, dy, dz, x=0, y=0, z=0):
    return Part.makeBox(dx, dy, dz, V(x, y, z))

def cbox(dx, dy, dz, cx=0, cy=0, cz=0):
    return Part.makeBox(dx, dy, dz, V(cx - dx / 2, cy - dy / 2, cz - dz / 2))

def cyl(r, h, x=0, y=0, z=0, d=V(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), d)

def cylY(r, y0, y1, x=0, z=0):
    """cylindre d'axe Y entre y0 et y1"""
    return Part.makeCylinder(r, abs(y1 - y0), V(x, min(y0, y1), z), V(0, 1, 0))

def rrect_face(dx, dy, r, cx=0, cy=0, z=0):
    x0, y0, x1, y1 = cx - dx / 2, cy - dy / 2, cx + dx / 2, cy + dy / 2
    if r <= 0:
        return Part.Face(Part.makePolygon([V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z), V(x0, y0, z)]))
    n = V(0, 0, 1)
    e = [Part.makeLine(V(x0 + r, y0, z), V(x1 - r, y0, z)),
         Part.makeCircle(r, V(x1 - r, y0 + r, z), n, 270, 360),
         Part.makeLine(V(x1, y0 + r, z), V(x1, y1 - r, z)),
         Part.makeCircle(r, V(x1 - r, y1 - r, z), n, 0, 90),
         Part.makeLine(V(x1 - r, y1, z), V(x0 + r, y1, z)),
         Part.makeCircle(r, V(x0 + r, y1 - r, z), n, 90, 180),
         Part.makeLine(V(x0, y1 - r, z), V(x0, y0 + r, z)),
         Part.makeCircle(r, V(x0 + r, y0 + r, z), n, 180, 270)]
    return Part.Face(Part.Wire(Part.__sortEdges__(e)))

def rrect(dx, dy, dz, r, cx=0, cy=0, z0=0):
    return rrect_face(dx, dy, r, cx, cy, z0).extrude(V(0, 0, dz))

def hexprism(af, h, cx=0, cy=0, z0=0):
    rc = af / 2 / math.cos(math.radians(30))
    pts = [V(cx + rc * math.cos(math.radians(60 * k)), cy + rc * math.sin(math.radians(60 * k)), z0) for k in range(6)]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, h))

def rotX(s, deg):  s = s.copy(); s.rotate(V(), V(1, 0, 0), deg); return s
def rotY(s, deg):  s = s.copy(); s.rotate(V(), V(0, 1, 0), deg); return s
def rotZ(s, deg):  s = s.copy(); s.rotate(V(), V(0, 0, 1), deg); return s
def mv(s, x=0, y=0, z=0): s = s.copy(); s.translate(V(x, y, z)); return s

def fuse(*shapes):
    shapes = [s for s in shapes if s is not None]
    r = shapes[0]
    if len(shapes) > 1:
        r = r.multiFuse(shapes[1:])
    return r.removeSplitter()

def cut(base, *tools):
    r = base
    for t in tools:
        r = r.cut(t)
    return r.removeSplitter()

def entonnoir_x(x_bouche, sens, l, h, c_l, c_h, cy=0.0, cz=0.0):
    """Évasement d'entrée (chanfrein) d'un canal rectangulaire l × h d'axe X : loft entre la section agrandie
    (l + 2 c_l, h + 2 c_h) dans le plan de la bouche et la section nominale à max(c_l, c_h) vers l'intérieur
    (sens = +1 : l'intérieur du canal est vers +X). À soustraire du corps."""
    p = max(c_l, c_h)
    return loft_rects([(x_bouche - sens * 0.01, l + 2 * c_l, h + 2 * c_h, cy, cz), (x_bouche + sens * p, l, h, cy, cz)])

def loft_rects(sections):
    """sections = [(x, dy, dz, cy, cz), ...] → loft de rectangles dans des plans X = cte"""
    wires = []
    for x, dy, dz, cy, cz in sections:
        pts = [V(x, cy - dy / 2, cz - dz / 2), V(x, cy + dy / 2, cz - dz / 2), V(x, cy + dy / 2, cz + dz / 2),
               V(x, cy - dy / 2, cz + dz / 2)]
        pts.append(pts[0])
        wires.append(Part.makePolygon(pts))
    return Part.makeLoft(wires, True, True)

# =============================================================================================
# 3. ÉLÉMENTS FONCTIONNELS : crantage (rosette), filetage imprimé
# =============================================================================================
def couronne_dents(r1, r2, n, h, phase=0.0):
    """Couronne de n dents radiales triangulaires (profil 90°), base z=0, sommets z=h, axe Z.
    Chaque dent est un coin dont la largeur suit le pas local → deux couronnes décalées d'un demi-pas
    s'emboîtent exactement."""
    def tri(r):
        w = 2 * math.pi * r / n * 1.03
        return Part.makePolygon([V(r, -w / 2, 0), V(r, w / 2, 0), V(r, 0, h), V(r, -w / 2, 0)])
    dent = Part.makeLoft([tri(r1 - 0.6), tri(r2 + 0.6)], True, True)
    dents = []
    for k in range(n):
        d = dent.copy(); d.rotate(V(), V(0, 0, 1), phase + 360.0 * k / n); dents.append(d)
    ring = fuse(*dents)
    ann = cyl(r2, h + 0.2, z=-0.1).cut(cyl(r1, h + 0.4, z=-0.2))
    return ring.common(ann).removeSplitter()

def rayon_filet(u, r_maj, prof, pas, crete, fond):
    """Rayon du filet à l'écart axial u du centre de crête : profil trapézoïdal (crête plate, flancs ~30°, fond plat)."""
    wb = pas - fond
    u = abs(u)
    if u <= crete / 2:
        return r_maj
    if u >= wb / 2:
        return r_maj - prof
    return r_maj - prof * (u - crete / 2) / ((wb - crete) / 2)

def section_filet(z, r_maj, prof, pas, crete, fond, N, echelle=1.0):
    """Section transversale (plan z) de la tige filetée : polygone dont le rayon suit le profil de filet
    en fonction de l'angle — la section tourne avec z (filet à droite)."""
    pts = []
    for k in range(N):
        th = 2 * math.pi * k / N
        u = (z - pas * th / (2 * math.pi)) % pas
        if u > pas / 2:
            u -= pas
        r = rayon_filet(u, r_maj, prof, pas, crete, fond) * echelle
        pts.append(V(r * math.cos(th), r * math.sin(th), z))
    pts.append(pts[0])
    return Part.makePolygon(pts)

def tige_filetee(r_maj, longueur, z0=0.0, pointe=0.0):
    """Tige filetée M(2·r_maj) pas vis_pas, de z0 à z0+longueur, construite par loft lisse de sections complètes
    (noyau inclus : aucun booléen fragile). pointe > 0 : cône d'extrémité obtenu en réduisant les dernières sections.
    La crête du filet passe par l'angle 0 en z = 0 (phase absolue → alignement vis/écrou calculable)."""
    pas, prof = P["vis_pas"], P["vis_prof"]
    n = int(round(longueur / pas * P["filet_sections_par_pas"]))
    wires = []
    for j in range(n + 1):
        z = z0 + longueur * j / n
        ech = 1.0
        if pointe > 0 and z > z0 + longueur - pointe:
            ech = 1.0 - 0.28 * (z - (z0 + longueur - pointe)) / pointe
        wires.append(section_filet(z, r_maj, prof, pas, P["vis_crete"], P["vis_fond"], P["filet_points"], ech))
    return Part.makeLoft(wires, True, False, False)

def vis_molettee(L):
    """Vis M8 pas 2 à tête moletée Ø18 (12 crans) et fente pour pièce de monnaie ; tige par loft, pointe conique.
    Imprimée tête en bas. Le filet est engagé de 1 mm dans la tête (fusion robuste)."""
    h = P["vis_tete_h"]
    tete = cyl(P["vis_tete_d"] / 2, h)
    for k in range(12):
        g = cyl(1.3, h + 2, x=P["vis_tete_d"] / 2 + 0.2, z=-1)
        g.rotate(V(), V(0, 0, 1), 30 * k); tete = tete.cut(g)
    tete = tete.cut(cbox(P["vis_tete_d"] + 2, 1.6, 2.0, cz=1.0))
    tige = tige_filetee(FIL_R, L + 1.0, z0=h - 1.0, pointe=P["vis_pointe"])
    vis = tete.fuse(tige).removeSplitter()
    if not vis.isValid() or len(vis.Solids) != 1:
        log("ATTENTION : fusion tête/tige non valide → compound"); vis = Part.makeCompound([tete, tige])
    return vis

def outil_taraudage(L, z0=0.0):
    """« vis virtuelle » majorée du jeu radial vis_jeu, à soustraire d'un corps pour obtenir le taraudage."""
    return tige_filetee(FIL_R + P["vis_jeu"], L, z0=z0)

def controle_taraudage(nom, ecrou, z0, z1):
    """Vérifie qu'un écrou est bien taraudé : la matière doit alterner le long de z au rayon moyen du filet."""
    r = FIL_R + P["vis_jeu"] - P["vis_prof"] / 2
    ins = [ecrou.isInside(V(r, 0, z0 + (z1 - z0) * i / 60), 1e-4, True) for i in range(61)]
    trans = sum(1 for p, q in zip(ins, ins[1:]) if p != q)
    RAPPORT["verifications"].setdefault("taraudage_transitions", {})[nom] = trans
    if trans < 2:
        log(f"ATTENTION : {nom} ne présente pas de filet (transitions={trans})")
    return trans

def ecrou_rosette():
    """Écrou-rosette : corps hexagonal 13 (dans la poche de la noix), flasque conique à 45°, couronne
    de 24 dents sur la face tournée vers l'oreille. Repère : face de la noix en z=0, corps vers -z."""
    af = P["ecrou_hex"]; rc = af / 2 / math.cos(math.radians(30))
    corps = hexprism(af, P["ecrou_corps"], z0=-P["ecrou_corps"])
    h_cone = P["ecrou_flasque_r"] - rc
    cone = Part.makeCone(rc, P["ecrou_flasque_r"], h_cone)
    plat_h = P["jeu_AB"] - P["dents_h"] - h_cone
    plat = cyl(P["ecrou_flasque_r"], plat_h, z=h_cone)
    dents = couronne_dents(P["dents_r1"], P["dents_r2"], P["dents_n"], P["dents_h"], phase=180.0 / P["dents_n"])
    dents.translate(V(0, 0, h_cone + plat_h))
    body = fuse(corps, cone, plat, dents)
    L = P["ecrou_corps"] + P["jeu_AB"] + 2
    outil = outil_taraudage(L, z0=-P["ecrou_corps"] - 1)
    e = cut(body, outil)
    controle_taraudage("ecrou_rosette", e, -P["ecrou_corps"] + 0.3, P["jeu_AB"] - P["dents_h"] - 0.3)
    return e

def ecrou_hex():
    af = P["ecrou_hex"]
    body = hexprism(af, P["hexnut_h"])
    e = cut(body, outil_taraudage(P["hexnut_h"] + 2, z0=-1))
    controle_taraudage("ecrou_hex", e, 0.3, P["hexnut_h"] - 0.3)
    return e

def phase_vis(pl_vis, ecrou_place, L, n_test=36):
    """Angle (°) de rotation de la vis autour de son axe pour lequel ses crêtes de filet ne pénètrent pas
    l'écrou déjà placé : échantillonnage de points de crête (repère vis) → test d'appartenance à l'écrou."""
    pas, h = P["vis_pas"], P["vis_tete_h"]
    r = FIL_R - 0.05
    zs = [h + 0.5 + (L - 1.0) * i / 24 for i in range(25)]
    n_test = 72
    n_in_par_phase = []
    for k in range(n_test):
        phi = 360.0 * k / n_test
        pl = pl_vis.multiply(Placement(V(), Rot(V(0, 0, 1), phi)))
        n_in = 0
        for z in zs:
            th = 2 * math.pi * z / pas
            p = pl.multVec(V(r * math.cos(th), r * math.sin(th), z))
            if ecrou_place.isInside(p, 1e-3, True):
                n_in += 1
        n_in_par_phase.append(n_in)
    # centre de la plus longue plage circulaire de phases « libres » (aucune crête dans la matière de l'écrou)
    libres = [n == 0 for n in n_in_par_phase]
    if not any(libres):
        k = min(range(n_test), key=lambda i: n_in_par_phase[i])
        return 360.0 * k / n_test, n_in_par_phase[k]
    meilleur, longueur = 0, 0
    for start in range(n_test):
        if libres[start] and not libres[start - 1]:
            L_ = 0
            while libres[(start + L_) % n_test] and L_ < n_test:
                L_ += 1
            if L_ > longueur:
                meilleur, longueur = start, L_
    if longueur >= n_test:            # toutes les phases libres (ne devrait pas arriver avec un vrai filet)
        return 0.0, 0
    centre = (meilleur + (longueur - 1) / 2.0) % n_test
    RAPPORT["verifications"].setdefault("plage_phase_libre_deg", []).append(round(360.0 * longueur / n_test, 1))
    return round(360.0 * centre / n_test, 1), 0

# =============================================================================================
# 4. NOIX (côté tête / tourelle) et FOURCHE (côté bras)
# =============================================================================================
def mat_from_axes(ex, ey, ez, origin=V()):
    m = App.Matrix()
    m.A11, m.A21, m.A31 = ex.x, ex.y, ex.z
    m.A12, m.A22, m.A32 = ey.x, ey.y, ey.z
    m.A13, m.A23, m.A33 = ez.x, ez.y, ez.z
    m.A14, m.A24, m.A34 = origin.x, origin.y, origin.z
    return m

def noix(clip_z_max=None, clip_z_min=None, col=None):
    """Deux plaques parallèles (épaisseur noix_ep) de part et d'autre de la fenêtre nappe (noix_gap),
    axe de charnière = axe Y à l'origine, corps hôte vers +X (face d'appui en X = noix_col).
    Plan de nappe : Z = 0 (l'axe est dans le plan de la nappe).
    Symétrique : chaque plaque porte une poche hexagonale (écrou-rosette) ouverte vers l'extérieur ;
    la charnière est serrée par une vis de chaque côté (plus de tourillon : montage par simple glissement)."""
    R, ep, gap = P["noix_R"], P["noix_ep"], P["noix_gap"]
    col = P["noix_col"] if col is None else col
    y_in = gap / 2
    zmax = R if clip_z_max is None else clip_z_max
    zmin = -R if clip_z_min is None else clip_z_min
    plaques = []
    for s in (+1, -1):
        y0 = min(s * y_in, s * (y_in + ep)); y1 = max(s * y_in, s * (y_in + ep))
        disque = cylY(R, y0, y1)
        cou = box(col, ep, zmax - zmin, 0, y0, zmin)
        pl = fuse(disque, cou)
        poche = rotX(hexprism(P["ecrou_hex"] + P["ecrou_jeu"], P["ecrou_poche"] + 0.5), -90 * s)   # +Z → s·Y
        poche.translate(V(0, s * (y_in + ep - P["ecrou_poche"]), 0))
        plaques.append(cut(pl, poche))
    return fuse(*plaques)

X_MANCHON0 = -34.0        # début du manchon (ouverture) — repère fourche
X_FOND_MANCHON = -13.0    # fond de l'emmanchement (extrémité du corps de bras)
X_GOUPILLE = -30.5

def piece_fourche():
    """Fourche (embout de bras) : axe de charnière = axe Y à l'origine, corps de bras vers -X.
    Oreilles 4 mm à |Y| ∈ [19, 23], rayon 11, symétriques en Z (axe dans le plan de nappe), toutes deux
    crantées (24 dents) sur leur face intérieure et alésées Ø8,6 (vis de chaque côté).
    Le corps de bras (24x8) s'emmanche sur 21 mm, ajustement serré 0,1 ; 2 goupilles Ø3 imprimées (ou colle).
    Bouche du canal côté fenêtre évasée (entonnoir) pour guider la nappe. Imprimée debout sur l'ouverture du manchon."""
    R, ep, f = P["oreille_R"], P["oreille_ep"], P["fen_demi"]
    jeu = P["manchon_jeu"]
    man_l = P["bras_l"] + 2 * (P["manchon_ep"] + jeu)
    man_h = P["bras_h"] + 2 * (P["manchon_ep"] + jeu)
    x_bloc0 = -(f + 8.0)                    # -19
    x_ev0 = x_bloc0 - 8.0                   # -27
    oreilles = []
    for s in (+1, -1):
        y0 = min(s * Y_A, s * OREILLE_OUT); y1 = max(s * Y_A, s * OREILLE_OUT)
        o = fuse(cylY(R, y0, y1), box(-x_bloc0, ep, 2 * R, x_bloc0, y0, -R))
        o = cut(o, cylY(P["oreille_trou"] / 2, y0 - 1, y1 + 1))
        dents = rotX(couronne_dents(P["dents_r1"], P["dents_r2"], P["dents_n"], P["dents_h"]), 90 * s)  # +Z → -s·Y (vers l'axe)
        dents.translate(V(0, s * Y_A, 0))
        o = fuse(o, dents)
        oreilles.append(o)
    bloc = box(-f - x_bloc0, FOURCHE_L, 2 * R, x_bloc0, -OREILLE_OUT, -R)
    evas = loft_rects([(x_ev0, man_l, man_h, 0, 0), (x_bloc0, FOURCHE_L, 2 * R, 0, 0)])
    manchon = box(x_ev0 - X_MANCHON0, man_l, man_h, X_MANCHON0, -man_l / 2, -man_h / 2)
    fk = fuse(*oreilles, bloc, evas, manchon)
    # encoche centrale du bloc racine : entre les oreilles (|Y| < 16) on ne garde que la section du corps (Z ±4),
    # ce qui dégage la face arrière de la tête (ou le collier) jusqu'à ~130° de pliage
    for sz in (+1, -1):
        fk = fk.cut(box(-f - x_bloc0 + 0.02, 32.0, R, x_bloc0 - 0.01, -16.0, min(sz * P["bras_h"] / 2, sz * (R + 1))))
    logement = box(X_FOND_MANCHON - X_MANCHON0 + 1, P["bras_l"] + 2 * jeu, P["bras_h"] + 2 * jeu,
                   X_MANCHON0 - 1, -(P["bras_l"] / 2 + jeu), -(P["bras_h"] / 2 + jeu))
    fk = cut(fk, logement)
    canal = box(-f - X_FOND_MANCHON + 0.5 + 0.01, P["canal_l"], P["canal_h"], X_FOND_MANCHON - 0.5,
                -P["canal_l"] / 2, -P["canal_h"] / 2)
    fk = cut(fk, canal)
    # entonnoirs : bouche côté fenêtre (X = -fen_demi, 1,5 en Z / 1 en Y) et côté fond de manchon (0,5)
    fk = cut(fk, entonnoir_x(-f, -1, P["canal_l"], P["canal_h"], 1.0, P["chanf_fenetre"]),
             entonnoir_x(X_FOND_MANCHON, +1, P["canal_l"], P["canal_h"], 0.5, 0.5))
    for s in (+1, -1):
        fk = cut(fk, cylY(P["goupille_d"] / 2, s * (P["canal_l"] / 2), s * (man_l / 2 + 1), x=X_GOUPILLE))
    return fk.removeSplitter()

# =============================================================================================
# 5. PIÈCES
# =============================================================================================
def piece_bras_corps(L):
    """Corps de bras : barre 24x8 à canal fermé 18x2,4, longueur L - 2x13 (emmanchée de 21 mm à chaque bout),
    bouches de canal chanfreinées (entonnoir chanf_canal)."""
    Lc = L + 2 * X_FOND_MANCHON
    c = box(Lc, P["bras_l"], P["bras_h"], 0, -P["bras_l"] / 2, -P["bras_h"] / 2)
    c = cut(c, box(Lc + 2, P["canal_l"], P["canal_h"], -1, -P["canal_l"] / 2, -P["canal_h"] / 2))
    ch = P["chanf_canal"]
    c = cut(c, entonnoir_x(0.0, +1, P["canal_l"], P["canal_h"], ch, ch), entonnoir_x(Lc, -1, P["canal_l"], P["canal_h"], ch, ch))
    xg = X_GOUPILLE - X_FOND_MANCHON      # -17.5 → 17.5 mm de chaque extrémité
    for x in (-xg, Lc + xg):
        for s in (+1, -1):
            c = cut(c, cylY(P["goupille_d"] / 2, s * (P["canal_l"] / 2 - 0.5), s * (P["bras_l"] / 2 + 1), x=x))
    return c.removeSplitter()

def piece_goupille():
    """Goupille imprimée Ø3 x 7 à tête (retient le corps de bras dans la fourche ; alternative : colle)."""
    g = fuse(cyl(P["goupille_d"] / 2 - 0.15, 6.8), cyl(3.0, 1.2, z=6.8))
    return g

def chanfreins_alesage(z_haut, z_bas):
    """Deux cônes à 45° (chanf_fut) sur les arêtes haute et basse de l'alésage Ø20 du fût : la nappe n'y frotte
    jamais sur une arête vive (torsion de lacet, montage)."""
    r = P["fut_alesage"] / 2; c = P["chanf_fut"]
    haut = Part.makeCone(r, r + c + 0.01, c + 0.01, V(0, 0, z_haut - c), V(0, 0, 1))
    bas = Part.makeCone(r + c + 0.01, r, c + 0.01, V(0, 0, z_bas - 0.01), V(0, 0, 1))
    return [haut, bas]

def piece_pied_couvercle():
    """Pied pour fixation sur couvercle : fût creux à l'origine, platine pied_cx × pied_cy décalée de pied_decal vers +y
    (le bord -y de la platine affleure la face extérieure de la paroi du boîtier ; la nappe monte à 16 mm du bord).
    4 fentes 3,4 × 8 (vis M3 ou goupilles collées)."""
    cx, cy, ep = P["pied_cx"], P["pied_cy"], P["pied_ep"]
    pl = rrect(cx, cy, ep, 4.0, cy=P["pied_decal"], z0=-ep)
    for sx in (+1, -1):
        for yy in (P["fente_y_av"], P["fente_y_ar"]):
            pl = pl.cut(rrect(P["fente_l"], P["fente_L"], ep + 2, P["fente_l"] / 2 - 0.01, sx * P["fente_x"], yy, -ep - 1))
    fut = cyl(P["fut_d"] / 2, P["fut_h"])
    tenon = cyl(P["tenon_d"] / 2, P["tenon_h"], z=P["fut_h"])
    conge = Part.makeCone(P["fut_d"] / 2 + 3, P["fut_d"] / 2, 3.0)
    conge = conge.common(box(cx, cy, 10, -cx / 2, P["pied_decal"] - cy / 2, -1))   # le congé ne déborde pas de la platine
    pied = fuse(pl, fut, tenon, conge)
    return cut(pied, cyl(P["fut_alesage"] / 2, 60, z=-30), *chanfreins_alesage(P["fut_h"] + P["tenon_h"], -ep))

def gabarit_couvercle_2d():
    """Motif de perçage du couvercle (repère : centre du fût) : contour de platine, trou nappe, 4 trous de vis."""
    cx, cy, d = P["pied_cx"], P["pied_cy"], P["pied_decal"]
    trous = [(sx * P["fente_x"], yy, 3.4) for sx in (+1, -1) for yy in (P["fente_y_av"], P["fente_y_ar"])]
    return dict(contour=(-cx / 2, d - cy / 2, cx / 2, d + cy / 2), nappe=(0.0, 0.0, P["couvercle_trou"]), vis=trous)

def piece_gabarit_couvercle():
    """Gabarit de perçage imprimable (plaque 1,2 mm) : à poser sur le couvercle pour pointer les 5 trous."""
    g = gabarit_couvercle_2d(); x0, y0, x1, y1 = g["contour"]
    pl = rrect(x1 - x0, y1 - y0, P["gabarit_ep"], 4.0, cy=(y0 + y1) / 2)
    pl = pl.cut(cyl(g["nappe"][2] / 2, 10, z=-5))
    for x, y, dia in g["vis"]:
        pl = pl.cut(cyl(dia / 2, 10, x, y, -5))
    return pl.removeSplitter()

def ecrire_gabarit_dxf_svg(dossier):
    g = gabarit_couvercle_2d(); x0, y0, x1, y1 = g["contour"]
    cercles = [g["nappe"]] + g["vis"]
    # DXF R12 minimal (mm)
    L = ["0", "SECTION", "2", "ENTITIES"]
    for (ax, ay, bx, by) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        L += ["0", "LINE", "8", "CONTOUR", "10", f"{ax:.3f}", "20", f"{ay:.3f}", "30", "0", "11", f"{bx:.3f}", "21", f"{by:.3f}", "31", "0"]
    for (x, y, dia) in cercles:
        L += ["0", "CIRCLE", "8", "TROUS", "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0", "40", f"{dia / 2:.3f}"]
    L += ["0", "ENDSEC", "0", "EOF"]
    with open(os.path.join(dossier, "gabarit_couvercle.dxf"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    w, h = x1 - x0, y1 - y0
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="{x0} {-y1} {w} {h}">',
         f'<rect x="{x0}" y="{-y1}" width="{w}" height="{h}" rx="4" fill="none" stroke="black" stroke-width="0.3"/>']
    for (x, y, dia) in cercles:
        S.append(f'<circle cx="{x}" cy="{-y}" r="{dia / 2}" fill="none" stroke="black" stroke-width="0.3"/>')
        S.append(f'<text x="{x + dia / 2 + 1}" y="{-y}" font-size="2.2" font-family="sans-serif">Ø{dia:g}</text>')
    S.append("</svg>")
    with open(os.path.join(dossier, "gabarit_couvercle.svg"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(S) + "\n")

def piece_pied_plat_centre():
    """Variante : platine carrée 46 × 46 centrée sur le fût (surface d'accueil large)."""
    c, ep = P["pied_c"], P["pied_ep"]
    pl = rrect(c, c, ep, 4.0, z0=-ep)
    for sx in (+1, -1):
        for sy in (+1, -1):
            pl = pl.cut(rrect(P["fente_L"], P["fente_l"], ep + 2, P["fente_l"] / 2 - 0.01,
                              sx * P["fente_pos"], sy * P["fente_pos"], -ep - 1))
    fut = cyl(P["fut_d"] / 2, P["fut_h"])
    tenon = cyl(P["tenon_d"] / 2, P["tenon_h"], z=P["fut_h"])
    conge = Part.makeCone(P["fut_d"] / 2 + 3, P["fut_d"] / 2, 3.0)
    pied = fuse(pl, fut, tenon, conge)
    pied = cut(pied, cyl(P["fut_alesage"] / 2, 60, z=-30), *chanfreins_alesage(P["fut_h"] + P["tenon_h"], -ep))
    return pied

def piece_cavalier_adaptateur():
    """Adaptateur « cavalier » : platine 46x46 à cheval sur une paroi verticale (épaisseur mur_ep),
    2 trous Ø3,4 (vis M3 ou goupilles collées) pour recevoir le pied plat ; passage nappe Ø22.
    Imprimé retourné (platine sur le plateau, joues vers le haut) : aucun surplomb."""
    c, ep = P["pied_c"], P["pied_ep"]
    pl = rrect(c, c, ep, 4.0, z0=-ep)
    pl = pl.cut(cyl(P["fut_alesage"] / 2 + 1, 20, z=-10))
    for sx in (+1, -1):
        pl = pl.cut(cyl(1.7, 20, sx * P["fente_pos"], P["fente_pos"], -10))
    g = P["mur_ep"] + 0.4
    y_ext0 = -c / 2
    ext = box(c, P["cavalier_ep"], P["cavalier_h"], -c / 2, y_ext0, -ep - P["cavalier_h"])
    y_int0 = y_ext0 + P["cavalier_ep"] + g
    inte = box(c, P["cavalier_ep"], P["cavalier_int_h"], -c / 2, y_int0, -ep - P["cavalier_int_h"])
    ad = fuse(pl, ext, inte)
    for sx in (+1, -1):
        ad = ad.cut(cylY(1.7, -c / 2 - 1, y_int0 + P["cavalier_ep"] + 1, x=sx * 15.0, z=-ep - P["cavalier_int_h"] / 2))
    return ad.removeSplitter()

def piece_bague():
    r_in = P["tenon_d"] / 2 + P["bague_jeu"]
    b = cyl(P["bague_d"] / 2, P["tenon_h"]).cut(cyl(r_in, P["tenon_h"] + 2, z=-1))
    return b.removeSplitter()

M_NOIX_EPAULE = mat_from_axes(V(0, 0, -1), V(0, 1, 0), V(1, 0, 0))   # repère noix → monde (col vers -Z)

def piece_collier():
    """Collier-tourelle (lacet) : anneau fendu serré sur le fût par une vis imprimée, noix d'épaule
    au-dessus (axe horizontal Y à la hauteur collier_h + noix_col, à l'aplomb du fût)."""
    ro = P["collier_d"] / 2; ri = P["fut_d"] / 2 + P["collier_jeu"]; h = P["collier_h"]
    anneau = cyl(ro, h).cut(cyl(ri, h + 2, z=-1))
    x1 = -(ro + P["patte_L"]); x0 = -ro + 2.0
    pattes = []
    for s in (+1, -1):
        y0 = min(s * 1.0, s * (1.0 + P["patte_l"])); y1 = max(s * 1.0, s * (1.0 + P["patte_l"]))
        pattes.append(box(x0 - x1, y1 - y0, P["patte_h"], x1, y0, (h - P["patte_h"]) / 2))
    col = fuse(anneau, *pattes)
    fente = box(ro + P["patte_L"] + 1, P["fente_collier"], h + 2, -(ro + P["patte_L"] + 1), -P["fente_collier"] / 2, -1)
    col = col.cut(fente)
    xv = -(ro + P["patte_L"] / 2 + 1.0); zv = h / 2
    col = col.cut(cylY(P["oreille_trou"] / 2, -20, 20, x=xv, z=zv))
    poche = rotX(hexprism(P["ecrou_hex"] + P["ecrou_jeu"], P["ecrou_poche"] + 0.5), -90)   # +Z → +Y
    poche.translate(V(xv, 1.0 + P["patte_l"] - P["ecrou_poche"], zv))
    col = col.cut(poche)
    n = noix(col=P["noix_col_epaule"]).transformGeometry(M_NOIX_EPAULE)
    n.translate(V(X_AXE_EPAULE, 0, Z_AXE_EPAULE))
    n = n.common(box(200, 200, 200, -100, -100, h - 0.5))
    col = fuse(col, n)
    col = col.cut(cyl(ri, h + 2, z=-1))
    return col.removeSplitter()

def piece_tete_coque():
    """Coque arrière : logement PCB, plots + pions aux 4 trous (référence rigide de la caméra, solidaire de la charnière),
    fente nappe à bouches évasées dans la paroi basse, épaulement de jupe, rainures d'encliquetage, noix de charnière
    symétrique sous la paroi basse. Imprimée sur sa paroi haute (les disques de noix dépassent de 5,2 mm derrière le fond)."""
    Lt, Ht = TETE_L, TETE_H
    ext = rrect(Lt, Ht, Z_COQUE, 3.0)
    poche = rrect(POCHE_L, POCHE_H, Z_COQUE, 1.0, z0=P["fond"])
    coque = ext.cut(poche)
    jz = Z_COQUE - P["jupe_h"]
    epaul = rrect(Lt + 2, Ht + 2, Z_COQUE, 3.0, z0=jz).cut(
        rrect(Lt - 2 * P["jupe_ep"], Ht - 2 * P["jupe_ep"], Z_COQUE + 2, 3.0 - P["jupe_ep"], z0=jz - 1))
    coque = coque.cut(epaul)
    xr = Lt / 2 - P["jupe_ep"]
    for s in (+1, -1):
        r = cbox(P["crochet"] + 0.1 + 0.4, P["crochet_L"] + 0.4, 1.0, s * (xr - (P["crochet"] + 0.1) / 2 + 0.2), 0, jz + 1.3)
        coque = coque.cut(r)
    for sx in (+1, -1):
        for yy in (TROU_Y_HAUT, TROU_Y_BAS):
            coque = coque.fuse(cyl(P["plot_d"] / 2, Z_PCB_DOS - P["fond"] + 0.01, sx * TROU_X, yy, P["fond"]))
            coque = coque.fuse(cyl(P["pion_d"] / 2, P["pion_h"], sx * TROU_X, yy, Z_PCB_DOS))
    fente = cbox(P["canal_l"], P["paroi"] + 2, P["canal_h"], 0, -(POCHE_H / 2 + P["paroi"] / 2), Z_NAPPE_TETE)
    cf = P["chanf_fente"]
    ent_int = rotZ(entonnoir_x(0.0, +1, P["canal_l"], P["canal_h"], cf, cf), -90)   # bouche côté logement, intérieur vers -y
    ent_int.translate(V(0, -POCHE_H / 2, Z_NAPPE_TETE))
    ent_ext = rotZ(entonnoir_x(0.0, +1, P["canal_l"], P["canal_h"], cf, cf), 90)    # bouche côté fenêtre, intérieur vers +y
    ent_ext.translate(V(0, -(POCHE_H / 2 + P["paroi"]), Z_NAPPE_TETE))
    n = noix(clip_z_max=TETE_P - Z_AXE_TETE, clip_z_min=-Z_AXE_TETE)
    n = rotZ(n, 90)                         # X_noix → +y_tête, Y_noix → -x_tête
    n.translate(V(0, Y_AXE_TETE, Z_AXE_TETE))
    coque = fuse(coque, n)
    coque = cut(coque, fente, ent_int, ent_ext)
    return coque.removeSplitter()

def piece_tete_facade():
    """Façade-capot : jupe emboîtée sur l'épaulement, 2 crochets, plaque avant avec ouverture optique chanfreinée
    à 45° côté avant, 4 fûts d'appui sur les trous du PCB dépassant de pcb_serrage. Chaque fût est porté par une
    languette-ressort découpée dans la plaque (fente en U de ressort_fente, traversante : verticale à l'impression),
    de sorte que le PCB est plaqué sur les plots de la coque avec une précontrainte tolérante aux cotes FDM.
    Fûts hauts : languettes le long de x, encastrées vers le centre ; fûts bas : languettes le long de y, encastrées
    vers la paroi basse. Imprimée face avant sur le plateau."""
    Lt, Ht = TETE_L, TETE_H
    jz = Z_COQUE - P["jupe_h"]
    cap = rrect(Lt, Ht, TETE_P - jz, 3.0, z0=jz)
    cav1 = rrect(Lt - 2 * P["jupe_ep"] + 2 * P["jupe_jeu"], Ht - 2 * P["jupe_ep"] + 2 * P["jupe_jeu"],
                 Z_COQUE + 0.2 - jz + 1, 3.0 - P["jupe_ep"], z0=jz - 1)
    cav2 = rrect(POCHE_L, POCHE_H, Z_FACADE_INT - (Z_COQUE - 0.8), 1.0, z0=Z_COQUE - 0.8)
    cap = cap.cut(cav1).cut(cav2)
    xr = Lt / 2 - P["jupe_ep"] + P["jupe_jeu"]
    for s in (+1, -1):
        pts = [V(s * xr, -P["crochet_L"] / 2, jz + 0.8), V(s * xr, -P["crochet_L"] / 2, jz + 1.8),
               V(s * (xr - P["crochet"]), -P["crochet_L"] / 2, jz + 1.8), V(s * xr, -P["crochet_L"] / 2, jz + 0.8)]
        cro = Part.Face(Part.makePolygon(pts)).extrude(V(0, P["crochet_L"], 0))
        cap = cap.fuse(cro)
    o, r, c = P["ouverture"], P["ouverture_r"], P["ouverture_chanfrein"]
    cap = cap.cut(rrect(o, o, 10, r, OBJ_C.x, OBJ_C.y, Z_FACADE_INT - 5))
    w_in = rrect_face(o, o, r, OBJ_C.x, OBJ_C.y, TETE_P - c).OuterWire
    w_out = rrect_face(o + 2 * c + 0.02, o + 2 * c + 0.02, r + c, OBJ_C.x, OBJ_C.y, TETE_P + 0.01).OuterWire
    cap = cap.cut(Part.makeLoft([w_in, w_out], True, True))
    w, sl = P["ressort_l"], P["ressort_fente"]
    zf0, zf1 = Z_FACADE_INT - 1.0, TETE_P + 1.0
    for sx in (+1, -1):
        # languette haute (le long de x) : racine en |x| = ressort_x0, bout en |x| = ressort_x1, fente haute affleurant la paroi
        x0, x1 = P["ressort_x0"], P["ressort_x1"]
        xa, xb = min(sx * x0, sx * (x1 + sl)), max(sx * x0, sx * (x1 + sl))
        yb = TROU_Y_HAUT - w / 2
        cap = cap.cut(box(xb - xa, sl, zf1 - zf0, xa, yb - sl, zf0))                              # fente basse
        cap = cap.cut(box(xb - xa, POCHE_H / 2 + 0.5 - (yb + w), zf1 - zf0, xa, yb + w, zf0))    # fente haute → paroi
        xt0, xt1 = min(sx * x1, sx * (x1 + sl)), max(sx * x1, sx * (x1 + sl))
        cap = cap.cut(box(xt1 - xt0, POCHE_H / 2 + 0.5 - (yb - sl), zf1 - zf0, xt0, yb - sl, zf0))   # fente de bout
        # languette basse (le long de y) : racine en y = ressort_y0 (vers la paroi basse), bout en y = ressort_y1
        y0, y1 = P["ressort_y0"], P["ressort_y1"]
        xl = sx * TROU_X - w / 2
        cap = cap.cut(box(sl, y1 + sl - y0, zf1 - zf0, xl - sl, y0, zf0))
        cap = cap.cut(box(sl, y1 + sl - y0, zf1 - zf0, xl + w, y0, zf0))
        cap = cap.cut(box(w + 2 * sl, sl, zf1 - zf0, xl - sl, y1, zf0))
    for sx in (+1, -1):
        for yy in (TROU_Y_HAUT, TROU_Y_BAS):
            cap = cap.fuse(cyl(P["plot_d"] / 2, Z_FACADE_INT - Z_PCB_AV + 0.5 + P["pcb_serrage"], sx * TROU_X, yy,
                               Z_PCB_AV - P["pcb_serrage"]))
    return cap.removeSplitter()

def piece_pcb_cm3():
    """Maquette d'encombrement Camera Module 3 (assemblage / rendus uniquement)."""
    pcb = rrect(P["pcb_l"], P["pcb_h"], P["pcb_ep"], 1.5, z0=Z_PCB_DOS)
    for sx in (+1, -1):
        for yy in (TROU_Y_HAUT, TROU_Y_BAS):
            pcb = pcb.cut(cyl(P["trou_d"] / 2, 5, sx * TROU_X, yy, Z_PCB_DOS - 2))
    obj = rrect(P["objectif_c"], P["objectif_c"], P["objectif_h"], 1.0, OBJ_C.x, OBJ_C.y, Z_PCB_AV)
    lentille = cyl(3.2, 0.3, OBJ_C.x, OBJ_C.y, Z_PCB_AV + P["objectif_h"] - 0.3)
    conn = cbox(P["connecteur_l"], P["connecteur_p"], P["connecteur_h"], 0, -P["pcb_h"] / 2 + P["connecteur_p"] / 2,
                Z_PCB_DOS - P["connecteur_h"] / 2)
    return fuse(pcb, obj, conn).cut(lentille).removeSplitter()

# =============================================================================================
# 6. GÉNÉRATION, CONTRÔLES, EXPORTS
# =============================================================================================
def infos(nom, s):
    bb = s.BoundBox
    d = dict(valide=bool(s.isValid()), volume_cm3=round(s.Volume / 1000.0, 2),
             encombrement=[round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)],
             solides=len(s.Solids))
    RAPPORT["pieces"][nom] = d
    log(f"{nom:24s} valide={d['valide']} vol={d['volume_cm3']} cm3 bbox={d['encombrement']} solides={d['solides']}")
    return d

def export_piece(nom, shape, orientation_impression=None, doc_desc=""):
    """FCStd + STEP (repère de conception) + STL (orienté pour l'impression, posé en Z=0)."""
    doc = App.newDocument(nom)
    o = doc.addObject("Part::Feature", nom); o.Shape = shape; o.Label = nom
    sh = doc.addObject("Spreadsheet::Sheet", "Parametres")
    sh.set("A1", "Paramètre"); sh.set("B1", "Valeur"); sh.set("C1", "Description")
    sh.set("C2", doc_desc)
    r = 2
    for k, v in P.items():
        sh.set(f"A{r}", k); sh.set(f"B{r}", str(v)); r += 1
    doc.recompute()
    doc.saveAs(os.path.join(OUT, "fcstd", nom + ".FCStd"))
    import Import
    Import.export([o], os.path.join(OUT, "step", nom + ".step"))
    s2 = shape.copy()
    if orientation_impression is not None:
        s2 = s2.transformGeometry(orientation_impression.toMatrix())
    bb = s2.BoundBox; s2.translate(V(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    import MeshPart
    m = MeshPart.meshFromShape(Shape=s2, LinearDeflection=0.04, AngularDeflection=0.26)
    m.write(os.path.join(OUT, "stl", nom + ".stl"))
    m0 = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.04, AngularDeflection=0.26)
    m0.write(os.path.join(OUT, "stl_conception", nom + ".stl"))
    App.closeDocument(doc.Name)

def placement_bras(psi, theta):
    """Repère bras → monde. Plan vertical d'azimut psi ; theta = angle depuis la verticale
    (0 = bras vertical, 90 = horizontal vers +X si psi = 0). Origine locale = axe d'épaule."""
    t, p = math.radians(theta), math.radians(psi)
    ex = V(math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t))
    ez = V(-math.cos(t) * math.cos(p), -math.cos(t) * math.sin(p), math.sin(t))
    ey = ez.cross(ex)
    axe_monde = V(X_AXE_EPAULE * math.cos(p), X_AXE_EPAULE * math.sin(p), Z_AXE_EPAULE)
    return Placement(mat_from_axes(ex, ey, ez, axe_monde - ez * E))

def placement_tete(pl_bras, L, beta):
    """Tête à l'extrémité du bras, pliée de beta autour de l'axe Y du bras (0 = tête dans le prolongement,
    beta > 0 : la tête bascule du côté -Z du bras, l'objectif regarde alors vers l'avant du bras)."""
    pl = pl_bras.multiply(Placement(V(L, 0, E), Rot()))
    pl = pl.multiply(Placement(V(), Rot(V(0, 1, 0), beta)))
    pl = pl.multiply(Placement(V(), Rot(V(0, 0, 1), -90)))
    pl = pl.multiply(Placement(V(0, -Y_AXE_TETE, -Z_AXE_TETE), Rot()))
    return pl

def placer(shape, pl):
    return shape.transformGeometry(pl.toMatrix())

def main():
    L = P["bras_L"]
    log("FreeCAD", ".".join(App.Version()[:3]), "→", OUT)
    pieces = {}
    log("génération des pièces…")
    corps_key = "04a_bras_corps_L%d" % int(L)
    pieces["01_pied_couvercle"] = piece_pied_couvercle()
    pieces["01a_pied_plat_centre"] = piece_pied_plat_centre()
    pieces["01b_cavalier_adaptateur"] = piece_cavalier_adaptateur()
    pieces["01c_gabarit_percage_couvercle"] = piece_gabarit_couvercle()
    ecrire_gabarit_dxf_svg(OUT)
    pieces["02_bague_retenue"] = piece_bague()
    pieces["03_collier_tourelle"] = piece_collier()
    pieces[corps_key] = piece_bras_corps(L)
    pieces["04a_bras_corps_L%d_alt" % int(P["bras_L_alt"])] = piece_bras_corps(P["bras_L_alt"])
    pieces["04b_fourche_x2"] = piece_fourche()
    pieces["04c_goupille_x4"] = piece_goupille()
    pieces["05_tete_coque"] = piece_tete_coque()
    pieces["06_tete_facade"] = piece_tete_facade()
    pieces["07_vis_M8_L11_x4"] = vis_molettee(P["vis_L_art"])
    pieces["08_vis_M8_L20"] = vis_molettee(P["vis_L_collier"])
    pieces["09_ecrou_rosette_x4"] = ecrou_rosette()
    pieces["10_ecrou_hex"] = ecrou_hex()
    pieces["90_maquette_cm3"] = piece_pcb_cm3()
    for k, s in pieces.items():
        infos(k, s)

    orient = {
        "01_pied_couvercle": Placement(), "01a_pied_plat_centre": Placement(), "01c_gabarit_percage_couvercle": Placement(),
        "01b_cavalier_adaptateur": Placement(V(), Rot(V(1, 0, 0), 180)),   # platine sur le plateau, joues en haut
        "02_bague_retenue": Placement(),
        "03_collier_tourelle": Placement(),
        corps_key: Placement(),                                            # à plat
        "04b_fourche_x2": Placement(V(), Rot(V(0, 1, 0), -90)),            # debout : -X (manchon) → -Z ? voir note
        "04c_goupille_x4": Placement(V(), Rot(V(1, 0, 0), 180)),           # tête sur le plateau
        "05_tete_coque": Placement(V(), Rot(V(1, 0, 0), -90)),             # paroi haute sur le plateau, noix en haut
        "06_tete_facade": Placement(V(), Rot(V(1, 0, 0), 180)),            # face avant sur le plateau
        "07_vis_M8_L11_x4": Placement(), "08_vis_M8_L20": Placement(),
        "09_ecrou_rosette_x4": Placement(V(), Rot(V(1, 0, 0), 0)),
        "10_ecrou_hex": Placement(),
        "90_maquette_cm3": Placement(),
    }
    # fourche debout : l'ouverture du manchon (X = -34) doit être sur le plateau → -X → -Z, i.e. X → +Z : Rot(Y, -90)
    # vérification numérique de l'orientation (le point le plus bas doit être l'ouverture du manchon)
    fk_o = pieces["04b_fourche_x2"].transformGeometry(orient["04b_fourche_x2"].toMatrix())
    assert abs(fk_o.BoundBox.ZMin - X_MANCHON0) < 1e-6, fk_o.BoundBox
    # écrou-rosette : corps hexagonal vers le bas (z<0 dans son repère) → déjà « tête en haut » : dents vers le haut
    desc = {
        "01_pied_couvercle": "Pied pour couvercle : platine 50x46 décalée (bord affleurant la paroi), 4 fentes 3,4x8, fût creux Ø26/Ø20 à arêtes chanfreinées, tenon Ø24",
        "01a_pied_plat_centre": "Variante : platine 46x46 centrée sur le fût",
        "01c_gabarit_percage_couvercle": "Gabarit de perçage du couvercle (plaque 1,2 mm) : trou nappe Ø22 + 4 trous Ø3,4",
        "01b_cavalier_adaptateur": "Adaptateur à cheval sur une paroi verticale (mur_ep) recevant le pied plat (2 trous Ø3,4)",
        "02_bague_retenue": "Bague emmanchée/collée sur le tenon : retient axialement le collier (jeu 0,5)",
        "03_collier_tourelle": "Collier fendu de lacet (serrage par vis imprimée M8) portant la noix d'épaule",
        corps_key: "Corps de bras 24x8, canal fermé 18x2,4 à bouches chanfreinées, 2 trous de goupille par extrémité",
        "04b_fourche_x2": "Embout-fourche (x2) : manchon 21 mm (serré 0,1), oreilles R11 crantées des deux côtés, alésages Ø8,6, bouche de canal évasée",
        "04c_goupille_x4": "Goupille Ø3 imprimée (x4) — facultative si collage",
        "05_tete_coque": "Coque arrière Camera Module 3 : logement PCB, plots/pions (référence rigide), fente nappe évasée, noix symétrique",
        "06_tete_facade": "Façade encliquetable : ouverture optique 14 chanfreinée, 4 fûts d'appui sur languettes-ressorts plaquant le PCB (0,2)",
        "07_vis_M8_L11_x4": "Vis moletée imprimée M8 pas 2, L=11 (x4, deux par articulation)",
        "08_vis_M8_L20": "Vis moletée imprimée M8 pas 2, L=20 (collier de lacet)",
        "09_ecrou_rosette_x4": "Écrou-rosette 24 dents (x4) : hexagone 13 × 3,5 dans la noix, dents vers l'oreille",
        "10_ecrou_hex": "Écrou hexagonal 13 imprimé (collier)",
        "90_maquette_cm3": "Encombrement Camera Module 3 (référence — ne pas imprimer)",
    }
    log("exports FCStd / STEP / STL…")
    for k, s in pieces.items():
        export_piece(k, s, orient.get(k), desc.get(k, ""))

    # ------------------------------------------------------------------------------------------
    # ASSEMBLAGE
    # ------------------------------------------------------------------------------------------
    psi, theta, beta = P["pose_lacet"], P["pose_epaule"], P["pose_tete"]
    pl_bras = placement_bras(psi, theta)
    pl_tete = placement_tete(pl_bras, L, beta)
    pl_collier = Placement(V(), Rot(V(0, 0, 1), psi))
    pl_f1 = pl_bras.multiply(Placement(V(), Rot(V(0, 1, 0), 180)))            # fourche épaule : corps vers +X, oreille A en +Y
    pl_f2 = pl_bras.multiply(Placement(V(L, 0, 0), Rot()))
    pl_corps = pl_bras.multiply(Placement(V(-X_FOND_MANCHON, 0, 0), Rot()))
    placed = {
        "pied": (pieces["01_pied_couvercle"], Placement()),
        "bague": (pieces["02_bague_retenue"], Placement(V(0, 0, P["fut_h"]), Rot())),
        "collier": (pieces["03_collier_tourelle"], pl_collier),
        "bras_corps": (pieces[corps_key], pl_corps),
        "fourche_epaule": (pieces["04b_fourche_x2"], pl_f1),
        "fourche_tete": (pieces["04b_fourche_x2"], pl_f2),
        "tete_coque": (pieces["05_tete_coque"], pl_tete),
        "tete_facade": (pieces["06_tete_facade"], pl_tete),
        "cm3": (pieces["90_maquette_cm3"], pl_tete),
    }
    def pl_noix_epaule():
        m = App.Matrix(M_NOIX_EPAULE); m.A14, m.A24, m.A34 = X_AXE_EPAULE, 0, Z_AXE_EPAULE
        return pl_collier.multiply(Placement(m))
    def pl_noix_tete():
        return pl_tete.multiply(Placement(V(0, Y_AXE_TETE, Z_AXE_TETE), Rot(V(0, 0, 1), 90)))
    yA = P["noix_gap"] / 2 + P["noix_ep"]
    phases = {}
    for nom, pln in (("epaule", pl_noix_epaule()), ("tete", pl_noix_tete())):
        for s, suf in ((+1, ""), (-1, "_B")):
            pl_e = pln.multiply(Placement(V(0, s * yA, 0), Rot(V(1, 0, 0), -90 * s)))      # dents vers l'oreille (s·Y)
            placed["ecrou_" + nom + suf] = (pieces["09_ecrou_rosette_x4"], pl_e)
            pl_v = pln.multiply(Placement(V(0, s * (OREILLE_OUT + P["vis_tete_h"]), 0), Rot(V(1, 0, 0), 90 * s)))
            phi, n_in = phase_vis(pl_v, placer(pieces["09_ecrou_rosette_x4"], pl_e), P["vis_L_art"])
            phases["vis_" + nom + suf] = (phi, n_in)
            placed["vis_" + nom + suf] = (pieces["07_vis_M8_L11_x4"], pl_v.multiply(Placement(V(), Rot(V(0, 0, 1), phi))))
    ro = P["collier_d"] / 2; xv = -(ro + P["patte_L"] / 2 + 1.0); zv = P["collier_h"] / 2
    pl_e = pl_collier.multiply(Placement(V(xv, 1.0 + P["patte_l"] - P["ecrou_poche"] + 0.25, zv), Rot(V(1, 0, 0), -90)))
    placed["ecrou_collier"] = (pieces["10_ecrou_hex"], pl_e)
    pl_v = pl_collier.multiply(Placement(V(xv, -(1.0 + P["patte_l"]) - P["vis_tete_h"], zv), Rot(V(1, 0, 0), -90)))
    phi, n_in = phase_vis(pl_v, placer(pieces["10_ecrou_hex"], pl_e), P["vis_L_collier"])
    phases["vis_collier"] = (phi, n_in)
    placed["vis_collier"] = (pieces["08_vis_M8_L20"], pl_v.multiply(Placement(V(), Rot(V(0, 0, 1), phi))))
    RAPPORT["verifications"]["phase_vis_deg_et_points_de_crete_dans_ecrou"] = phases
    # goupilles (4) : tête à l'extérieur des manchons
    for nom, plf in (("epaule", pl_f1), ("tete", pl_f2)):
        for s in (+1, -1):
            yg = s * (P["bras_l"] / 2 + P["manchon_ep"] + P["manchon_jeu"])
            rot = Rot(V(1, 0, 0), 90 if s > 0 else -90)      # +Z → -Y (s>0) / +Y (s<0) : pointe vers le canal
            placed[f"goupille_{nom}_{'A' if s > 0 else 'B'}"] = (pieces["04c_goupille_x4"], plf.multiply(
                Placement(V(X_GOUPILLE, yg + s * 6.8, 0), rot)))

    doc = App.newDocument("assemblage")
    import MeshPart
    for nom, (s, pl) in placed.items():
        o = doc.addObject("Part::Feature", nom); o.Shape = s; o.Placement = pl; o.Label = nom
        m = MeshPart.meshFromShape(Shape=placer(s, pl), LinearDeflection=0.05, AngularDeflection=0.3)
        m.write(os.path.join(OUT, "stl_assemblage", nom + ".stl"))
    # poses supplémentaires (rendus) : corps + fourches + tête + collier, sans visserie
    for pose_nom, (ps_, th_, be_) in {"repos": (0, 0, 0), "horizontal": (0, 90, 90), "lacet45": (45, 60, 120), "plongee": (0, 90, 150)}.items():
        d_ = os.path.join(OUT, "stl_assemblage", "pose_" + pose_nom); os.makedirs(d_, exist_ok=True)
        plb_ = placement_bras(ps_, th_); plt_ = placement_tete(plb_, L, be_); plc_ = Placement(V(), Rot(V(0, 0, 1), ps_))
        sub = {"pied": (pieces["01_pied_couvercle"], Placement()), "bague": (pieces["02_bague_retenue"], Placement(V(0, 0, P["fut_h"]), Rot())),
               "collier": (pieces["03_collier_tourelle"], plc_), "bras_corps": (pieces[corps_key], plb_.multiply(Placement(V(-X_FOND_MANCHON, 0, 0), Rot()))),
               "fourche_epaule": (pieces["04b_fourche_x2"], plb_.multiply(Placement(V(), Rot(V(0, 1, 0), 180)))),
               "fourche_tete": (pieces["04b_fourche_x2"], plb_.multiply(Placement(V(L, 0, 0), Rot()))),
               "tete_coque": (pieces["05_tete_coque"], plt_), "tete_facade": (pieces["06_tete_facade"], plt_), "cm3": (pieces["90_maquette_cm3"], plt_)}
        for nom, (s, pl) in sub.items():
            MeshPart.meshFromShape(Shape=placer(s, pl), LinearDeflection=0.05, AngularDeflection=0.3).write(os.path.join(d_, nom + ".stl"))
    sh = doc.addObject("Spreadsheet::Sheet", "Pose")
    for i, (k, v) in enumerate((("lacet (°)", psi), ("épaule (° depuis la verticale)", theta), ("tête (° de pliage)", beta),
                                ("bras_L (entraxe)", L)), start=1):
        sh.set(f"A{i}", k); sh.set(f"B{i}", str(v))
    doc.recompute()
    doc.saveAs(os.path.join(OUT, "fcstd", "00_assemblage.FCStd"))

    # ------------------------------------------------------------------------------------------
    # VÉRIFICATIONS
    # ------------------------------------------------------------------------------------------
    verif = RAPPORT["verifications"]
    pa = pl_bras.Base
    pt = pl_tete.multiply(Placement(V(0, Y_AXE_TETE, Z_AXE_TETE), Rot())).Base
    pb = pl_bras.multiply(Placement(V(L, 0, 0), Rot())).Base
    verif["axe_epaule_monde"] = [round(c, 3) for c in pa]
    verif["axe_tete_ecart_mm"] = round((pt - pb).Length, 4)
    def visee(theta_, beta_):
        plt = placement_tete(placement_bras(0.0, theta_), L, beta_)
        d = plt.Rotation.multVec(V(0, 0, 1))
        return round(math.degrees(math.asin(max(-1, min(1, d.z)))), 1), round(d.x, 2)
    verif["visee_elevation_deg_et_composante_avant"] = {f"epaule{th}_tete{be}": visee(th, be)
                                                        for th in (45, 60, 90) for be in (60, 90, 120, 150)}
    fixe = fuse(placer(pieces["01_pied_couvercle"], Placement()),
                placer(pieces["02_bague_retenue"], Placement(V(0, 0, P["fut_h"]), Rot())),
                placer(pieces["03_collier_tourelle"], pl_collier))
    def bras_complet(plb):
        return fuse(placer(pieces[corps_key], plb.multiply(Placement(V(-X_FOND_MANCHON, 0, 0), Rot()))),
                    placer(pieces["04b_fourche_x2"], plb.multiply(Placement(V(), Rot(V(0, 1, 0), 180)))),
                    placer(pieces["04b_fourche_x2"], plb.multiply(Placement(V(L, 0, 0), Rot()))))
    inter = {}
    def com(a, b):
        c = a.common(b)
        if c.Volume > 0.5:
            sol = [s for s in c.Solids if s.Volume > 0.01]
            bb = sol[0].BoundBox if sol else c.BoundBox
            for s in sol[1:]:
                bb.add(s.BoundBox)
            return [round(c.Volume, 3), [round(v, 1) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)]]
        return round(c.Volume, 3)
    for th in (0, 30, 60, 90, 100, 105, 110, 120):
        inter[f"bras_vs_base_epaule{th}"] = com(fixe, bras_complet(placement_bras(0.0, th)))
    plb60 = placement_bras(0.0, 60); b60 = bras_complet(plb60)
    for be in (0, 30, 60, 90, 120, 135, 150):
        plt = placement_tete(plb60, L, be)
        t = fuse(placer(pieces["05_tete_coque"], plt), placer(pieces["06_tete_facade"], plt))
        inter[f"tete_vs_bras_beta{be}"] = com(b60, t)
    # visserie vs fourches (état serré) et écrou vs noix, des deux côtés de chaque axe
    for nom, plf in (("epaule", pl_f1), ("tete", pl_f2)):
        fk = placer(pieces["04b_fourche_x2"], plf)
        for suf in ("", "_B"):
            ec = placer(*placed["ecrou_" + nom + suf])
            vi = placer(*placed["vis_" + nom + suf])
            inter[f"fourche_vs_ecrou_{nom}{suf}"] = round(fk.common(ec).Volume, 3)
            inter[f"fourche_vs_vis_{nom}{suf}"] = round(fk.common(vi).Volume, 3)
            inter[f"vis_vs_ecrou_{nom}{suf}(phase_alignee)"] = round(vi.common(ec).Volume, 3)
            inter[f"vis_vs_ecrou_{nom}{suf}(distance_mini_mm)"] = round(vi.distToShape(ec)[0], 3)
    # preuve de l'existence du filet : la même vis tournée d'un demi-tour (décalage d'un demi-pas) doit pénétrer l'écrou
    s_, pl_ = placed["vis_epaule"]
    vi180 = placer(s_, pl_.multiply(Placement(V(), Rot(V(0, 0, 1), 180))))
    inter["vis_vs_ecrou_epaule(phase+180deg)"] = round(vi180.common(placer(*placed["ecrou_epaule"])).Volume, 3)
    inter["fourche_epaule_vs_collier"] = round(placer(pieces["04b_fourche_x2"], pl_f1).common(placer(pieces["03_collier_tourelle"], pl_collier)).Volume, 3)
    inter["fourche_tete_vs_coque"] = com(placer(pieces["04b_fourche_x2"], pl_f2), placer(pieces["05_tete_coque"], pl_tete))
    inter["corps_vs_fourches"] = round(placer(pieces[corps_key], pl_corps).common(
        fuse(placer(pieces["04b_fourche_x2"], pl_f1), placer(pieces["04b_fourche_x2"], pl_f2))).Volume, 3)
    inter["cm3_vs_coque"] = round(placer(pieces["90_maquette_cm3"], pl_tete).common(placer(pieces["05_tete_coque"], pl_tete)).Volume, 3)
    inter["cm3_vs_facade(serrage_0.2_attendu)"] = round(placer(pieces["90_maquette_cm3"], pl_tete).common(placer(pieces["06_tete_facade"], pl_tete)).Volume, 3)
    inter["facade_vs_coque"] = round(placer(pieces["06_tete_facade"], pl_tete).common(placer(pieces["05_tete_coque"], pl_tete)).Volume, 3)
    verif["interferences_mm3"] = inter

    # ------------------------------------------------------------------------------------------
    # MONTAGE DE LA FOURCHE SUR LA NOIX : glissement suivant X avec les deux écrous enfoncés au fond des poches
    # (aucune interférence le long du trajet), puis écrous en position de travail (seul le recouvrement
    # volontaire de 3 % des dents subsiste).
    # ------------------------------------------------------------------------------------------
    enf = P["ecrou_poche"] - P["ecrou_corps"]                     # enfoncement possible de l'écrou (1,5)
    nx = noix(col=P["noix_col_epaule"])
    def ecrous_noix(sink):
        e = []
        for s in (+1, -1):
            e.append(placer(pieces["09_ecrou_rosette_x4"], Placement(V(0, s * (yA - sink), 0), Rot(V(1, 0, 0), -90 * s))))
        return fuse(*e)
    fk0 = pieces["04b_fourche_x2"]
    glisse = {}
    cible = fuse(nx, ecrous_noix(enf))
    for dx in (-30, -25, -20, -15, -10, -6, -3, -1, 0):
        glisse[f"dx{dx}"] = round(mv(fk0, dx, 0, 0).common(cible).Volume, 3)
    verif["montage_fourche_glissement_mm3"] = dict(enfoncement_ecrous_mm=enf, trajet=glisse,
                                                 position_travail_ecrous=round(fk0.common(fuse(nx, ecrous_noix(0.0))).Volume, 3),
                                                 fourche_vs_noix_seule=round(fk0.common(nx).Volume, 3),
                                                 jeu_dents_au_glissement_mm=round(Y_A - P["dents_h"] - (yA + P["jeu_AB"] - enf), 2))

    # ------------------------------------------------------------------------------------------
    # TENUE DU PCB : raideur des languettes-ressorts, précontrainte, dégagements objectif / ouverture
    # ------------------------------------------------------------------------------------------
    E_pla, E_petg = 3300.0, 2100.0
    t_r = P["facade_ep"]
    L_haut = TROU_X - P["ressort_x0"]
    L_bas = TROU_Y_BAS - P["ressort_y0"]
    I_r = P["ressort_l"] * t_r ** 3 / 12
    tol = 0.15
    def k(E, L_):
        return 3 * E * I_r / L_ ** 3
    k_tot_pla = 2 * (k(E_pla, L_haut) + k(E_pla, L_bas))
    k_tot_petg = 2 * (k(E_petg, L_haut) + k(E_petg, L_bas))
    verif["serrage_pcb"] = dict(
        languettes_mm=dict(largeur=P["ressort_l"], epaisseur=t_r, fente=P["ressort_fente"],
                           longueur_utile_hautes=round(L_haut, 2), longueur_utile_basses=round(L_bas, 2)),
        raideur_N_par_mm=dict(PLA_haute=round(k(E_pla, L_haut), 1), PLA_basse=round(k(E_pla, L_bas), 1),
                              PETG_haute=round(k(E_petg, L_haut), 1), PETG_basse=round(k(E_petg, L_bas), 1)),
        precontrainte_nominale_mm=P["pcb_serrage"],
        force_totale_N=dict(PLA=round(k_tot_pla * P["pcb_serrage"], 1), PETG=round(k_tot_petg * P["pcb_serrage"], 1)),
        plage_tolerance_empilage_mm=[round(P["pcb_serrage"] - tol, 2), round(P["pcb_serrage"] + tol, 2)],
        force_totale_N_pire_cas=dict(PLA=[round(k_tot_pla * (P["pcb_serrage"] - tol), 1), round(k_tot_pla * (P["pcb_serrage"] + tol), 1)]),
        deformation_max_pct=round(100 * 3 * t_r * (P["pcb_serrage"] + tol) / (2 * min(L_haut, L_bas) ** 2), 2),
        masse_pcb_g=4.0, acceleration_tenue_g=round(k_tot_pla * (P["pcb_serrage"] - tol) / (0.004 * 9.81), 0),
        reference_camera="PCB plaqué sur les 4 plots rigides de la coque (pièce qui porte la charnière) ; les pions Ø1,8 centrent",
    )
    verif["objectif"] = dict(
        hauteur_bloc_mm=P["objectif_h"], face_interieure_facade_au_dessus_pcb_mm=round(Z_FACADE_INT - Z_PCB_AV, 2),
        degagement_axial_mm=round(P["jeu_objectif"] + P["pcb_serrage"], 2),
        ouverture_mm=P["ouverture"], bloc_objectif_mm=P["objectif_c"],
        jeu_lateral_par_cote_mm=round((P["ouverture"] - P["objectif_c"]) / 2, 2),
        chanfrein_avant_mm=P["ouverture_chanfrein"],
        demi_angle_libre_deg=round(math.degrees(math.atan((P["ouverture"] / 2 - 2.5) / (P["jeu_objectif"] + P["pcb_serrage"] + P["facade_ep"] - P["ouverture_chanfrein"]))), 1),
        remarque="le bloc objectif ne touche jamais la façade : la caméra est référencée par son PCB (4 trous), serré sans jeu",
    )
    # ------------------------------------------------------------------------------------------
    # PASSAGES DE LA NAPPE ET DE SES CONNECTEURS (largeur 16 / épaisseur ≤ 0,6 avec raidisseur)
    # ------------------------------------------------------------------------------------------
    verif["passages_nappe"] = {
        "fente de tête (paroi basse)": f"{P['canal_l']:g} × {P['canal_h']:g}, entonnoirs {P['chanf_fente']:g} des deux côtés",
        "bouche de fourche côté fenêtre": f"{P['canal_l']:g} × {P['canal_h']:g} évasée à {P['canal_l'] + 2:g} × {P['canal_h'] + 2 * P['chanf_fenetre']:g}",
        "canal du corps": f"{P['canal_l']:g} × {P['canal_h']:g}, bouches chanfreinées {P['chanf_canal']:g}",
        "fenêtre de noix": f"{P['noix_gap']:g} entre plaques",
        "alésage du fût": f"Ø{P['fut_alesage']:g}, arêtes chanfreinées {P['chanf_fut']:g}",
        "trou du couvercle": f"Ø{P['couvercle_trou']:g} (à chanfreiner/ébavurer)",
        "connecteurs": "Standard 15 voies : 16 × ≈0,6 ; Mini 22 voies : ≤ 16 × ≈0,6 → passent partout",
        "verrou du connecteur CM3": f"coulisse vers le bord bas du PCB : inopérable PCB en place (jeu {P['pcb_jeu_h'] / 2:g} mm) → brancher la nappe AVANT de poser le PCB",
    }
    # ------------------------------------------------------------------------------------------
    # VIBRATIONS : premier mode du bras (console 150 mm, masse en bout)
    # ------------------------------------------------------------------------------------------
    rho = 1.24e-3  # g/mm³ PLA
    m_tete = (pieces["05_tete_coque"].Volume + pieces["06_tete_facade"].Volume) * rho * 0.85 + 4.0 \
             + pieces["04b_fourche_x2"].Volume * rho * 0.6 + 2 * (pieces["07_vis_M8_L11_x4"].Volume + pieces["09_ecrou_rosette_x4"].Volume) * rho
    m_corps = pieces[corps_key].Volume * rho * 0.6
    I_faible = (P["bras_l"] * P["bras_h"] ** 3 - P["canal_l"] * P["canal_h"] ** 3) / 12
    I_fort = (P["bras_h"] * P["bras_l"] ** 3 - P["canal_h"] * P["canal_l"] ** 3) / 12
    def f1(E, I):
        k = 3 * E * I / L ** 3                         # N/mm
        return round(math.sqrt(k * 1000 / ((m_tete + 0.24 * m_corps) / 1000)) / (2 * math.pi), 0)
    verif["vibrations"] = dict(masse_en_bout_g=round(m_tete, 1), masse_corps_g=round(m_corps, 1),
                               f1_Hz=dict(PLA_plan_faible=f1(E_pla, I_faible), PLA_plan_fort=f1(E_pla, I_fort),
                                          PETG_plan_faible=f1(E_petg, I_faible)),
                               remarque="sources (pas, ventilateur du Pi 5 : 30-130 Hz) d'amplitude micrométrique ; sans jeu dans la chaîne, l'image ne bouge pas")
    # rayon de pliage de la nappe dans la fenêtre (corde entre sortie et entrée de canal, arc tangent)
    f = P["fen_demi"]
    rayons = {}
    for be in (30, 60, 90, 110, 120, 135):
        b = math.radians(be)
        corde = f * math.sqrt(2 + 2 * math.cos(b))
        rayons[f"beta{be}"] = round(corde / (2 * math.sin(b / 2)), 2)
    verif["rayon_pliage_nappe_mm"] = rayons
    trajet = {  # noqa
        "connecteur CAM Pi 5 → couvercle (≈ 35 mm mesurés sur photo + coude + insertion)": P["cable_boitier"],
        "couvercle → dessous de la platine (platine posée sur le couvercle)": P["cable_boitier_pied"],
        "platine → axe d'épaule (fût + collier + col)": P["pied_ep"] + Z_AXE_EPAULE,
        "bras (entraxe épaule → tête)": L,
        "axe tête → connecteur CM3 (col + paroi + dos PCB + insertion)": round(P["noix_col"] + P["paroi"] + (P["pcb_h"] / 2 - P["connecteur_p"]) + 4.0, 1),
        "réserve de courbure (2 charnières)": 6.0,
    }
    total = sum(trajet.values())
    verif["budget_nappe"] = dict(trajet=trajet, total_mm=round(total, 1), cable_mm=P["cable_L"], marge_mm=round(P["cable_L"] - total, 1))
    log("vérifications :", json.dumps(verif, ensure_ascii=False, indent=1))
    RAPPORT["duree_s"] = round(time.time() - T0, 1)
    with open(os.path.join(OUT, "rapport.json"), "w", encoding="utf-8") as fh:
        json.dump(RAPPORT, fh, ensure_ascii=False, indent=1)
    log("terminé en", RAPPORT["duree_s"], "s")

main()
