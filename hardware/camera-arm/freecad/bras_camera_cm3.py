# -*- coding: utf-8 -*-
"""
bras_camera_cm3.py — Bras articulé 3 axes + boîtier Camera Module 3, fixé sur le boîtier du RPi 5.

Macro FreeCAD paramétrique (module Part, API Python). Tout est régénéré à partir du dictionnaire P.
Exécution :
  * headless : OUT_DIR=/chemin/sortie freecadcmd -c "exec(open('bras_camera_cm3.py').read())"
  * dans FreeCAD : Macro > Macros… > Exécuter (les documents s'ouvrent, les exports vont dans OUT_DIR
    ou, à défaut, dans ~/bras_camera_out).

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
    # --- bras -------------------------------------------------------------------------------
    bras_L=float(os.environ.get("ARM_L", 150.0)),  # entraxe épaule → tête
    bras_l=24.0, bras_h=8.0,
    # --- articulation « fenêtre » commune (épaule et tête) -------------------------------------
    excentr=0.0,          # axe de charnière DANS le plan de nappe (trajet de nappe constant, pliage symétrique)
    fen_demi=11.0,        # nappe libre de chaque côté de l'axe = rayon des oreilles (rayon de pliage ≥ 6 mm jusqu'à 120°)
    noix_R=10.0, noix_ep=6.0, noix_gap=18.0, noix_col=12.0, noix_col_epaule=16.0,   # plaques de noix ; col plus haut à l'épaule (dégagement bague)
    oreille_ep=4.0, oreille_R=11.0, oreille_trou=8.6,        # oreilles de fourche (côté bras)
    manchon_L=21.0, manchon_ep=2.8, manchon_jeu=0.2, goupille_d=3.2,  # emmanchement corps de bras → fourche
    jeu_AB=4.0,           # écart face de noix → face d'oreille (A : écrou-rosette ; B : bossage + jeu)
    axe_d=8.0, boss_B_d=16.0, boss_B_ep=3.5, axe_long=3.5,
    dents_n=24, dents_h=1.0, dents_r1=6.5, dents_r2=10.0,
    ecrou_hex=13.0, ecrou_corps=4.5, ecrou_poche=5.0, ecrou_jeu=0.3, ecrou_flasque_r=10.0,
    # --- visserie imprimée M8 « pas gros » 2 mm --------------------------------------------
    vis_dmaj=7.8, vis_pas=2.0, vis_prof=0.9, vis_jeu=0.3, vis_tete_d=18.0, vis_tete_h=5.0,
    vis_L_art=11.0, vis_L_collier=20.0, hexnut_h=5.0,
    # --- tête : Raspberry Pi Camera Module 3 (standard) -----------------------------------
    pcb_l=25.0, pcb_h=23.862, pcb_ep=1.0, pcb_jeu_l=0.6, pcb_jeu_h=0.5,
    trou_d=2.2, trous_dx=21.0, trous_dy=12.5, trou_bord_haut=2.0,
    objectif_c=11.0, objectif_h=8.0, ouverture=13.0, ouverture_r=3.0,
    connecteur_l=20.5, connecteur_p=5.5, connecteur_h=3.0, nappe_z_conn=1.2,
    paroi=3.0, fond=2.0, jeu_dos=4.0, facade_ep=1.5, jeu_objectif=0.5, rebord=2.0,
    plot_d=3.6, pion_d=1.8, pion_h=1.0,
    jupe_ep=1.2, jupe_h=6.0, jupe_jeu=0.15, crochet=0.6, crochet_L=8.0,
    # --- pied, fût creux, collier-tourelle ----------------------------------------------------
    pied_c=46.0, pied_ep=4.0, fente_l=3.4, fente_L=8.0, fente_pos=17.0,
    fut_d=26.0, fut_alesage=20.0, fut_h=12.5, tenon_d=24.0, tenon_h=3.0, bague_d=32.0, bague_jeu=0.1,
    collier_d=34.0, collier_jeu=0.3, collier_h=12.0, fente_collier=2.0,
    patte_L=9.0, patte_l=8.0, patte_h=10.0,
    mur_ep=3.0, cavalier_h=25.0, cavalier_ep=4.0, cavalier_int_h=14.0,   # adaptateur « cavalier » (paroi verticale)
    # --- pose d'assemblage par défaut ---------------------------------------------------------
    pose_lacet=0.0, pose_epaule=60.0, pose_tete=120.0,
    # --- budget câble ------------------------------------------------------------------------
    cable_L=300.0, cable_boitier=60.0, cable_boitier_pied=20.0,
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

def filetage(r_maj, pas, longueur, prof, ovl=0.35, crete=0.35, fond=0.5):
    """Solide « vis » (noyau + filet hélicoïdal), axe Z, de z=0 à z=longueur."""
    r_root = r_maj - prof
    wb = pas - fond
    prof_pts = [V(r_root - ovl, 0, -wb / 2), V(r_maj, 0, -crete / 2), V(r_maj, 0, crete / 2),
                V(r_root - ovl, 0, wb / 2), V(r_root - ovl, 0, -wb / 2)]
    profile = Part.Wire(Part.makePolygon(prof_pts))
    h_tot = longueur + 2 * pas
    helix = Part.makeHelix(pas, h_tot, r_root)
    helix = helix if isinstance(helix, Part.Wire) else Part.Wire(helix)
    helix.translate(V(0, 0, -pas)); profile.translate(V(0, 0, -pas))
    sweep = helix.makePipeShell([profile], True, True)
    if not sweep.isValid():
        sweep.fix(0.01, 0.01, 0.01)
    core = cyl(r_root, longueur)
    fil = sweep.fuse(core)
    clip = cyl(r_maj + 1.0, longueur)
    return fil.common(clip).removeSplitter()

def vis_molettee(L):
    """Vis M8 pas 2 à tête moletée Ø18, fente pour pièce de monnaie. Imprimée tête en bas."""
    tete = cyl(P["vis_tete_d"] / 2, P["vis_tete_h"])
    for k in range(12):
        g = cyl(1.3, P["vis_tete_h"] + 2, x=P["vis_tete_d"] / 2 + 0.2, z=-1)
        g.rotate(V(), V(0, 0, 1), 30 * k); tete = tete.cut(g)
    tete = tete.cut(cbox(P["vis_tete_d"] + 2, 1.6, 2.0, cz=1.0))  # fente
    fil = filetage(FIL_R, P["vis_pas"], L, P["vis_prof"])
    # pointe chanfreinée
    cone = Part.makeCone(FIL_R + 0.3, FIL_R - P["vis_prof"] - 0.2, 1.2, V(0, 0, L - 1.2))
    fil = fil.common(fuse(cyl(FIL_R + 0.5, L - 1.2), cone))
    fil.translate(V(0, 0, P["vis_tete_h"]))
    return fuse(tete, fil)

def outil_taraudage(L):
    """« vis virtuelle » majorée du jeu, à soustraire d'un corps pour obtenir le taraudage."""
    return filetage(FIL_R + P["vis_jeu"], P["vis_pas"], L, P["vis_prof"])

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
    outil = outil_taraudage(L); outil.translate(V(0, 0, -P["ecrou_corps"] - 1))
    return cut(body, outil)

def ecrou_hex():
    af = P["ecrou_hex"]
    body = hexprism(af, P["hexnut_h"])
    outil = outil_taraudage(P["hexnut_h"] + 2); outil.translate(V(0, 0, -1))
    return cut(body, outil)

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
    Côté A (+Y) : poche hexagonale (écrou-rosette). Côté B (-Y) : bossage d'appui Ø16 + tourillon Ø8."""
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
        plaques.append(fuse(disque, cou))
    A, B = plaques
    poche = rotX(hexprism(P["ecrou_hex"] + P["ecrou_jeu"], P["ecrou_poche"] + 0.5), -90)   # +Z → +Y
    poche.translate(V(0, y_in + ep - P["ecrou_poche"], 0))
    A = cut(A, poche)
    yB = -(y_in + ep)
    boss = cylY(P["boss_B_d"] / 2, yB - P["boss_B_ep"], yB + 0.01)
    tour = cylY(P["axe_d"] / 2, yB - P["boss_B_ep"] - P["axe_long"], yB - P["boss_B_ep"] + 0.01)
    B = fuse(B, boss, tour)
    return fuse(A, B)

X_MANCHON0 = -34.0        # début du manchon (ouverture) — repère fourche
X_FOND_MANCHON = -13.0    # fond de l'emmanchement (extrémité du corps de bras)
X_GOUPILLE = -30.5

def piece_fourche():
    """Fourche (embout de bras) : axe de charnière = axe Y à l'origine, corps de bras vers -X.
    Oreilles 4 mm à |Y| ∈ [19, 23], rayon 11, symétriques en Z (axe dans le plan de nappe).
    Oreille A (+Y) : crantage 24 dents sur la face intérieure ; oreille B (-Y) : alésage lisse.
    Le corps de bras (24x8) s'emmanche sur 21 mm ; 2 goupilles Ø3 imprimées (ou colle).
    Imprimée debout sur l'ouverture du manchon : aucun surplomb."""
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
        if s > 0:
            dents = rotX(couronne_dents(P["dents_r1"], P["dents_r2"], P["dents_n"], P["dents_h"]), 90)  # +Z → -Y
            dents.translate(V(0, Y_A, 0))
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
    for s in (+1, -1):
        fk = cut(fk, cylY(P["goupille_d"] / 2, s * (P["canal_l"] / 2), s * (man_l / 2 + 1), x=X_GOUPILLE))
    return fk.removeSplitter()

# =============================================================================================
# 5. PIÈCES
# =============================================================================================
def piece_bras_corps(L):
    """Corps de bras : barre 24x8 à canal fermé 18x2,4, longueur L - 2x13 (emmanchée de 21 mm à chaque bout)."""
    Lc = L + 2 * X_FOND_MANCHON
    c = box(Lc, P["bras_l"], P["bras_h"], 0, -P["bras_l"] / 2, -P["bras_h"] / 2)
    c = cut(c, box(Lc + 2, P["canal_l"], P["canal_h"], -1, -P["canal_l"] / 2, -P["canal_h"] / 2))
    xg = X_GOUPILLE - X_FOND_MANCHON      # -17.5 → 17.5 mm de chaque extrémité
    for x in (-xg, Lc + xg):
        for s in (+1, -1):
            c = cut(c, cylY(P["goupille_d"] / 2, s * (P["canal_l"] / 2 - 0.5), s * (P["bras_l"] / 2 + 1), x=x))
    return c.removeSplitter()

def piece_goupille():
    """Goupille imprimée Ø3 x 7 à tête (retient le corps de bras dans la fourche ; alternative : colle)."""
    g = fuse(cyl(P["goupille_d"] / 2 - 0.15, 6.8), cyl(3.0, 1.2, z=6.8))
    return g

def piece_pied_plat():
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
    pied = cut(pied, cyl(P["fut_alesage"] / 2, 60, z=-30))
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
    """Coque arrière : logement PCB, plots + pions aux 4 trous, fente nappe dans la paroi basse,
    épaulement de jupe, rainures d'encliquetage, noix de charnière sous la paroi basse."""
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
    n = noix(clip_z_max=TETE_P - Z_AXE_TETE, clip_z_min=-Z_AXE_TETE)
    n = rotZ(n, 90)                         # X_noix → +y_tête, Y_noix → -x_tête
    n.translate(V(0, Y_AXE_TETE, Z_AXE_TETE))
    coque = fuse(coque, n)
    coque = coque.cut(fente)
    return coque.removeSplitter()

def piece_tete_facade():
    """Façade-capot : jupe emboîtée sur l'épaulement, 2 crochets, plaque avant avec ouverture optique,
    4 fûts d'appui sur les trous du PCB. Imprimée face avant sur le plateau."""
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
    cap = cap.cut(rrect(P["ouverture"], P["ouverture"], 10, P["ouverture_r"], OBJ_C.x, OBJ_C.y, Z_FACADE_INT - 5))
    for sx in (+1, -1):
        for yy in (TROU_Y_HAUT, TROU_Y_BAS):
            cap = cap.fuse(cyl(P["plot_d"] / 2, Z_FACADE_INT - Z_PCB_AV + 0.5, sx * TROU_X, yy, Z_PCB_AV))
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
    pieces["01_pied_plat"] = piece_pied_plat()
    pieces["01b_cavalier_adaptateur"] = piece_cavalier_adaptateur()
    pieces["02_bague_retenue"] = piece_bague()
    pieces["03_collier_tourelle"] = piece_collier()
    pieces[corps_key] = piece_bras_corps(L)
    pieces["04b_fourche_x2"] = piece_fourche()
    pieces["04c_goupille_x4"] = piece_goupille()
    pieces["05_tete_coque"] = piece_tete_coque()
    pieces["06_tete_facade"] = piece_tete_facade()
    pieces["07_vis_M8_L11_x2"] = vis_molettee(P["vis_L_art"])
    pieces["08_vis_M8_L20"] = vis_molettee(P["vis_L_collier"])
    pieces["09_ecrou_rosette_x2"] = ecrou_rosette()
    pieces["10_ecrou_hex"] = ecrou_hex()
    pieces["90_maquette_cm3"] = piece_pcb_cm3()
    for k, s in pieces.items():
        infos(k, s)

    orient = {
        "01_pied_plat": Placement(),
        "01b_cavalier_adaptateur": Placement(V(), Rot(V(1, 0, 0), 180)),   # platine sur le plateau, joues en haut
        "02_bague_retenue": Placement(),
        "03_collier_tourelle": Placement(),
        corps_key: Placement(),                                            # à plat
        "04b_fourche_x2": Placement(V(), Rot(V(0, 1, 0), -90)),            # debout : -X (manchon) → -Z ? voir note
        "04c_goupille_x4": Placement(V(), Rot(V(1, 0, 0), 180)),           # tête sur le plateau
        "05_tete_coque": Placement(V(), Rot(V(1, 0, 0), -90)),             # paroi haute sur le plateau, noix en haut
        "06_tete_facade": Placement(V(), Rot(V(1, 0, 0), 180)),            # face avant sur le plateau
        "07_vis_M8_L11_x2": Placement(), "08_vis_M8_L20": Placement(),
        "09_ecrou_rosette_x2": Placement(V(), Rot(V(1, 0, 0), 0)),
        "10_ecrou_hex": Placement(),
        "90_maquette_cm3": Placement(),
    }
    # fourche debout : l'ouverture du manchon (X = -34) doit être sur le plateau → -X → -Z, i.e. X → +Z : Rot(Y, -90)
    # vérification numérique de l'orientation (le point le plus bas doit être l'ouverture du manchon)
    fk_o = pieces["04b_fourche_x2"].transformGeometry(orient["04b_fourche_x2"].toMatrix())
    assert abs(fk_o.BoundBox.ZMin - X_MANCHON0) < 1e-6, fk_o.BoundBox
    # écrou-rosette : corps hexagonal vers le bas (z<0 dans son repère) → déjà « tête en haut » : dents vers le haut
    desc = {
        "01_pied_plat": "Platine 46x46, 4 fentes 3,4x8 (vis M3 ou goupilles), fût creux Ø26/Ø20 (passage nappe), tenon Ø24",
        "01b_cavalier_adaptateur": "Adaptateur à cheval sur une paroi verticale (mur_ep) recevant le pied plat (2 trous Ø3,4)",
        "02_bague_retenue": "Bague emmanchée/collée sur le tenon : retient axialement le collier (jeu 0,5)",
        "03_collier_tourelle": "Collier fendu de lacet (serrage par vis imprimée M8) portant la noix d'épaule",
        corps_key: "Corps de bras 24x8, canal fermé 18x2,4 pour la nappe, 2 trous de goupille par extrémité",
        "04b_fourche_x2": "Embout-fourche (x2) : manchon 21 mm, oreilles R11 crantées côté A, alésage Ø8,6",
        "04c_goupille_x4": "Goupille Ø3 imprimée (x4) — facultative si collage",
        "05_tete_coque": "Coque arrière Camera Module 3 : logement PCB, plots/pions, fente nappe, noix de charnière",
        "06_tete_facade": "Façade encliquetable : ouverture optique 13 mm, 4 fûts d'appui sur le PCB",
        "07_vis_M8_L11_x2": "Vis moletée imprimée M8 pas 2, L=11 (x2, articulations)",
        "08_vis_M8_L20": "Vis moletée imprimée M8 pas 2, L=20 (collier de lacet)",
        "09_ecrou_rosette_x2": "Écrou-rosette 24 dents (x2) : hexagone 13 dans la noix, dents vers l'oreille",
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
        "pied": (pieces["01_pied_plat"], Placement()),
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
    for nom, pln in (("epaule", pl_noix_epaule()), ("tete", pl_noix_tete())):
        placed["ecrou_" + nom] = (pieces["09_ecrou_rosette_x2"], pln.multiply(Placement(V(0, yA, 0), Rot(V(1, 0, 0), -90))))
        placed["vis_" + nom] = (pieces["07_vis_M8_L11_x2"],
                                pln.multiply(Placement(V(0, OREILLE_OUT + P["vis_tete_h"], 0), Rot(V(1, 0, 0), 90))))
    ro = P["collier_d"] / 2; xv = -(ro + P["patte_L"] / 2 + 1.0); zv = P["collier_h"] / 2
    placed["vis_collier"] = (pieces["08_vis_M8_L20"], pl_collier.multiply(
        Placement(V(xv, -(1.0 + P["patte_l"]) - P["vis_tete_h"], zv), Rot(V(1, 0, 0), -90))))
    placed["ecrou_collier"] = (pieces["10_ecrou_hex"], pl_collier.multiply(
        Placement(V(xv, 1.0 + P["patte_l"] - P["ecrou_poche"] + 0.25, zv), Rot(V(1, 0, 0), -90))))
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
        sub = {"pied": (pieces["01_pied_plat"], Placement()), "bague": (pieces["02_bague_retenue"], Placement(V(0, 0, P["fut_h"]), Rot())),
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
    fixe = fuse(placer(pieces["01_pied_plat"], Placement()),
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
    # visserie vs fourches (état serré) et écrou vs noix
    for nom, pln, plf in (("epaule", pl_noix_epaule(), pl_f1), ("tete", pl_noix_tete(), pl_f2)):
        fk = placer(pieces["04b_fourche_x2"], plf)
        ec = placer(pieces["09_ecrou_rosette_x2"], pln.multiply(Placement(V(0, yA, 0), Rot(V(1, 0, 0), -90))))
        vi = placer(pieces["07_vis_M8_L11_x2"], pln.multiply(Placement(V(0, OREILLE_OUT + P["vis_tete_h"], 0), Rot(V(1, 0, 0), 90))))
        inter[f"fourche_vs_ecrou_{nom}"] = round(fk.common(ec).Volume, 3)
        inter[f"fourche_vs_vis_{nom}"] = round(fk.common(vi).Volume, 3)
        inter[f"vis_vs_ecrou_{nom}(filets_engages)"] = round(vi.common(ec).Volume, 3)
    inter["fourche_epaule_vs_collier"] = round(placer(pieces["04b_fourche_x2"], pl_f1).common(placer(pieces["03_collier_tourelle"], pl_collier)).Volume, 3)
    inter["fourche_tete_vs_coque"] = com(placer(pieces["04b_fourche_x2"], pl_f2), placer(pieces["05_tete_coque"], pl_tete))
    inter["corps_vs_fourches"] = round(placer(pieces[corps_key], pl_corps).common(
        fuse(placer(pieces["04b_fourche_x2"], pl_f1), placer(pieces["04b_fourche_x2"], pl_f2))).Volume, 3)
    inter["cm3_vs_coque+facade"] = round(placer(pieces["90_maquette_cm3"], pl_tete).common(
        fuse(placer(pieces["05_tete_coque"], pl_tete), placer(pieces["06_tete_facade"], pl_tete))).Volume, 3)
    verif["interferences_mm3"] = inter
    # rayon de pliage de la nappe dans la fenêtre (corde entre sortie et entrée de canal, arc tangent)
    f = P["fen_demi"]
    rayons = {}
    for be in (30, 60, 90, 110, 120, 135):
        b = math.radians(be)
        corde = f * math.sqrt(2 + 2 * math.cos(b))
        rayons[f"beta{be}"] = round(corde / (2 * math.sin(b / 2)), 2)
    verif["rayon_pliage_nappe_mm"] = rayons
    trajet = {  # noqa
        "connecteur Pi 5 → sortie du boîtier RPi (estimé, à mesurer)": P["cable_boitier"],
        "sortie boîtier → dessous de la platine (estimé, à mesurer)": P["cable_boitier_pied"],
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
