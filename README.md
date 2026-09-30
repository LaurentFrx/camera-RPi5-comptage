# camera-RPi5-comptage

Caméra de comptage sur Raspberry Pi 5 + AI HAT+ (Hailo) avec Camera Module 3.

## Contenu

* `hardware/camera-arm/` — **étude détaillée et CAO** du bras articulé 3 axes et du boîtier de la Camera Module 3, fixé sur le boîtier du Pi 5 et parcouru par la nappe caméra (pièces imprimables sur Prusa, quincaillerie métallique nulle par défaut).
  * `ETUDE.md` : l'étude complète (choix, cotes, vérifications, impression, montage).
  * `freecad/bras_camera_cm3.py` : macro FreeCAD paramétrique qui régénère toutes les pièces et les exports.
  * `export/` : fichiers natifs FreeCAD `.FCStd`, STEP, STL orientés impression, rapport de contrôle.
  * `renders/` : rendus et schémas cotés.
