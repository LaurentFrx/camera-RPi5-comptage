# -*- coding: utf-8 -*-
"""verif_filetage_freecad.py — contrôle géométrique de la visserie imprimée (à exécuter avec freecadcmd).
Usage : OUT_JSON=coupes_filet.json freecadcmd -c "exec(open('verif_filetage_freecad.py', encoding='utf-8').read())"
Construit la vis L11, l'écrou hexagonal et l'écrou-rosette avec les fonctions de bras_camera_cm3.py, affiche validité,
volumes, rayons/hauteurs réels (tessellation) et exporte les coupes axiales (plan y = 0) pour la figure."""
import os, json, math
import FreeCAD as App, Part
from FreeCAD import Vector as V
ICI = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
os.environ.setdefault("OUT_DIR", os.path.join(ICI, "_verif_tmp"))
src = open(os.path.join(ICI, "bras_camera_cm3.py"), encoding="utf-8").read()
src = src[:src.rfind("\nmain()")]
ns = {}; exec(compile(src, "bras", "exec"), ns); P = ns["P"]
def coupe(shape):
    out = []
    for w in shape.slice(V(0, 1, 0), 0.0):
        out.append([[round(p.x, 3), round(p.z, 3)] for p in w.discretize(Distance=0.05)])
    return out
v = ns["vis_molettee"](P["vis_L_art"]); eh = ns["ecrou_hex"](); er = ns["ecrou_rosette"]()
for nom, s in (("vis L11", v), ("ecrou hex", eh), ("ecrou rosette", er)):
    m = s.tessellate(0.05)[0]
    print(f"{nom:14s} valide={s.isValid()} solides={len(s.Solids)} faces={len(s.Faces)} vol={s.Volume:.1f} mm3  rmax={max(math.hypot(p.x, p.y) for p in m):.2f} zmin/zmax={min(p.z for p in m):.2f}/{max(p.z for p in m):.2f}")
json.dump({"vis": coupe(v), "ecrou_hex": coupe(eh), "ecrou_rosette": coupe(er),
           "P": {k: P[k] for k in ("vis_dmaj","vis_pas","vis_prof","vis_jeu","vis_crete","vis_fond","vis_tete_h","vis_L_art","hexnut_h","ecrou_corps")}},
          open(os.environ.get("OUT_JSON", os.path.join(ICI, "coupes_filet.json")), "w"))
print("coupes exportées")
