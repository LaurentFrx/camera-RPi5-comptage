# -*- coding: utf-8 -*-
"""
kit_calibration.py — kit d'essai du filetage imprimé : 1 vis M8 L11 + 1 écrou-rosette au jeu nominal (vis_jeu = 0,3 mm depuis l'essai du 01/10 : à 0,4 la vis flottait).
Avec JEUX="0.3,0.4,0.5", produit à la place un kit comparatif de 3 écrous marqués 1, 2 et 3 points. À exécuter avec freecadcmd :

  OUT_DIR=<dossier_export> freecadcmd -c "exec(open('kit_calibration.py', encoding='utf-8').read())"

Produit, dans <OUT_DIR>/stl :
  20_kit_calibration_plateau.stl           ← tout le kit disposé pour l'impression (vis tête en bas, écrous hexagone en bas)
  20_kit_calibration_ecrou_rosette_jeu03.stl / _jeu04.stl / _jeu05.stl   ← écrous séparés
et <OUT_DIR>/kit_calibration.json (volumes, contrôles).
"""
import os, sys, json, math
import FreeCAD as App
import Part, Mesh, MeshPart
from FreeCAD import Vector as V, Placement, Rotation as Rot

ICI = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.environ.get("OUT_DIR") or os.path.join(os.path.expanduser("~"), "bras_camera_out")
os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)

# charge les fonctions de la macro sans exécuter main()
src = open(os.path.join(ICI, "bras_camera_cm3.py"), encoding="utf-8").read()
src = src[:src.rfind("\nmain()")]
ns = {"__file__": os.path.join(ICI, "bras_camera_cm3.py")}
exec(compile(src, "bras_camera_cm3", "exec"), ns)
P = ns["P"]

# jeux radiaux à produire : par défaut le seul jeu nominal de la macro (vis_jeu) ; JEUX="0.3,0.4,0.5" pour un kit comparatif marqué
JEUX = [float(x) for x in os.environ.get("JEUX", str(P["vis_jeu"])).split(",")]
rapport = {"jeux": JEUX, "pieces": {}}

def points_marquage(ecrou, n):
    """n alvéoles Ø1,6 × 0,5 sur le pan d'hexagone de normale 30° (corps hexagonal, z ∈ [-corps, 0])."""
    af = P["ecrou_hex"]; a = math.radians(30)
    nx, ny = math.cos(a), math.sin(a)          # normale au pan
    tx, ty = -math.sin(a), math.cos(a)         # tangente au pan
    zc = -P["ecrou_corps"] / 2
    offs = {1: [0.0], 2: [-1.2, 1.2], 3: [-2.3, 0.0, 2.3]}[n]
    for s in offs:
        px, py = (af / 2 + 0.6) * nx + s * tx, (af / 2 + 0.6) * ny + s * ty
        ecrou = ecrou.cut(Part.makeCylinder(0.8, 1.1, V(px, py, zc), V(-nx, -ny, 0)))
    return ecrou

def mesh_de(shape, pl=None):
    s = shape if pl is None else shape.transformGeometry(pl.toMatrix())
    return MeshPart.meshFromShape(Shape=s, LinearDeflection=0.04, AngularDeflection=0.26)

def pose_plateau(shape):
    """pose la pièce sur z = 0, centrée en x/y"""
    bb = shape.BoundBox
    return Placement(V(-bb.Center.x, -bb.Center.y, -bb.ZMin), Rot())

plateau = Mesh.Mesh()
# --- la vis (le jeu ne la concerne pas : c'est l'écrou qui porte le jeu)
vis = ns["vis_molettee"](P["vis_L_art"])
pl = pose_plateau(vis)
m = mesh_de(vis, pl); plateau.addMesh(m)
rapport["pieces"]["vis_M8_L11"] = dict(valide=bool(vis.isValid()), volume_cm3=round(vis.Volume / 1000, 2))
print(f"[kit] vis L11 : valide={vis.isValid()} vol={vis.Volume/1000:.2f} cm3")

# --- les trois écrous-rosette
jeu_initial = P["vis_jeu"]
x = 0.0
for i, jeu in enumerate(JEUX, start=1):
    P["vis_jeu"] = jeu
    e = ns["ecrou_rosette"]()
    if len(JEUX) > 1:
        e = points_marquage(e, i)
    nom = f"20_kit_calibration_ecrou_rosette_jeu{int(round(jeu * 10)):02d}"
    pl = pose_plateau(e)
    me = mesh_de(e, pl)
    me.write(os.path.join(OUT, "stl", nom + ".stl"))
    x += 26.0
    me2 = mesh_de(e, Placement(pl.Base + V(x, 0, 0), Rot()))
    plateau.addMesh(me2)
    trans = ns["RAPPORT"]["verifications"].get("taraudage_transitions", {}).get("ecrou_rosette")
    rapport["pieces"][nom] = dict(jeu_radial=jeu, marquage_points=(i if len(JEUX) > 1 else 0), valide=bool(e.isValid()), volume_cm3=round(e.Volume / 1000, 2),
                                  taraudage_transitions=trans)
    print(f"[kit] écrou-rosette jeu {jeu} ({i} point(s)) : valide={e.isValid()} vol={e.Volume/1000:.2f} cm3 transitions={trans}")
P["vis_jeu"] = jeu_initial

plateau.write(os.path.join(OUT, "stl", "20_kit_calibration_plateau.stl"))
bb = plateau.BoundBox
rapport["plateau_mm"] = [round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)]
with open(os.path.join(OUT, "kit_calibration.json"), "w", encoding="utf-8") as fh:
    json.dump(rapport, fh, ensure_ascii=False, indent=1)
print(f"[kit] plateau {rapport['plateau_mm']} mm → {os.path.join(OUT, 'stl', '20_kit_calibration_plateau.stl')}")
