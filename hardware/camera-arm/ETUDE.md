# Étude détaillée — bras articulé 3 axes et boîtier pour Camera Module 3 sur boîtier Raspberry Pi 5

**Projet** : camera-RPi5-comptage · **Imprimante** : Prusa (Biscalab) · **Date** : 30/09/2026
**Livrables** : cette étude, la macro FreeCAD paramétrique (`freecad/bras_camera_cm3.py`), les fichiers natifs FreeCAD `.FCStd` (une pièce par fichier + un assemblage), les STEP, les STL orientés pour l'impression, les rendus et le rapport de contrôle (`export/rapport.json`).

> **Outillage — point important.** Cette session cloud n'avait **aucun connecteur MCP FreeCAD** : il n'en existe pas dans le registre de connecteurs claude.ai, et les « FreeCAD MCP » communautaires sont des ponts locaux vers une instance FreeCAD graphique tournant sur la machine de l'utilisateur. J'ai donc installé **FreeCAD lui-même** (paquet conda-forge, version 26.3) dans le conteneur et piloté son API Python en mode headless (`freecadcmd`), c'est-à-dire exactement ce qu'un connecteur MCP FreeCAD ferait sous le capot. Résultat : de vrais documents `.FCStd` ouvrables dans ton FreeCAD, et une macro que tu peux rejouer chez toi pour tout régénérer avec d'autres paramètres.

---

## 1. Résumé de la solution

![Assemblage](renders/01_assemblage_iso.png)

| Élément | Choix retenu | Pourquoi |
|---|---|---|
| Cinématique | **3 axes** : lacet (tourelle sur fût creux) + tangage d'épaule + tangage de tête | Pan/tilt indispensables pour viser une scène de comptage ; l'épaule règle hauteur et portée. Un 4ᵉ axe (coude) est possible sans changer les pièces (voir § 13). |
| Passage de la nappe | **Intérieur** : fût creux Ø20 → fenêtre entre les plaques de noix → canal fermé 18 × 2,4 dans le bras → fente de la tête | Nappe protégée, jamais pincée ; longueur de trajet quasi constante quel que soit l'angle car **l'axe de chaque charnière est dans le plan de la nappe**. |
| Articulations | Charnière « à fenêtre » : noix à 2 plaques + fourche à 2 oreilles, serrage par **vis moletée M8 imprimée** et **écrou-rosette 24 dents** (pas 15°) | Verrouillage positif (crantage) insensible au fluage du PETG, contrairement à une friction pure ; visserie 100 % imprimée. |
| Lacet | Collier fendu serré sur le fût par la même vis imprimée, bague de retenue emmanchée | Réglage continu 360° (limité par la torsion de nappe : ±90° conseillé), aucun filetage de grand diamètre à imprimer. |
| Bras | **Deux pièces** : corps plat 24 × 8 (longueur paramétrable) + 2 fourches identiques emmanchées 21 mm | Chaque pièce s'imprime **sans support** ; changer la longueur = réimprimer le seul corps. |
| Tête caméra | Coque + façade encliquetée ; PCB pris en **sandwich** sur ses 4 trous (plots + pions Ø1,8 à l'arrière, fûts à l'avant) | Zéro vis M2 ; respect de la zone interdite du flex autofocus. |
| Fixation au boîtier RPi5 | **Sur le couvercle** : pied à platine 50 × 46 dont le fût est décalé vers le bord (la platine affleure la paroi, la nappe monte à 16 mm du bord), 4 fentes 3,4 × 8 (2 à 4 vis M3 **ou** goupilles imprimées collées), trou Ø22 dans le couvercle sous le fût ; gabarit de perçage imprimable + DXF/SVG. Variantes : platine centrée, adaptateur « cavalier ». | Décision utilisateur du 30/09 : fixation sur couvercle. |
| Quincaillerie métallique | **Zéro par défaut**. Optionnel : 2 à 4 vis M3 pour la platine si tu préfères aux goupilles collées | Demande explicite du cahier des charges. |

**Plages validées par calcul d'interférences (aucune collision)** : épaule 0 → 100° depuis la verticale ; tête 0 → 135° de pliage ; lacet 360°. Plages **recommandées** (rayon de pliage de la nappe ≥ 6 mm) : épaule 0 → 95°, tête 0 → 120°.

**Budget câble** (nappe officielle Standard–Mini 300 mm, entraxe de bras 150 mm, platine posée sur le couvercle) : 258 mm consommés, **≈ 42 mm de marge** ; le tronçon dans le boîtier Pi (≈ 35 mm mesurés sur la photo du 30/09 + coude + insertion = 45 mm) reste à confirmer au montage. Un corps de bras alternatif d'entraxe **170 mm** est fourni (marge ≈ 22 mm).

---

## 2. Ce que les photos m'ont appris et les hypothèses retenues

| Observation (photos) | Conséquence pour la conception |
|---|---|
| **Raspberry Pi Camera Module 3** standard (autofocus IMX708, objectif carré ~11 mm, flex VCM noir remontant vers le bord haut). | Contour PCB 25,0 × 23,86 mm, 4 trous Ø2,2 à 21 × 12,5 mm, trous hauts à 2 mm du bord haut ; centre optique sur la ligne des trous bas, centré en largeur ; hauteur d'objectif ≈ 8 mm au-dessus du PCB (12,4 − 1 − 3). Module 3 **Wide** : objectif ≈ 9 mm → paramètre `objectif_h`. |
| Connecteur nappe **15 broches 1 mm** au dos, sur le bord bas ; nappe sortant vers le bas dans le plan de la carte ; composants dos ≤ 1,5 mm, connecteur ≈ 3 mm. | Dégagement dos 4 mm ; plan de nappe à 1,2 mm derrière le dos du PCB ; fente 18 × 2,4 dans la paroi basse de la coque. |
| Câble **« Raspberry Pi Camera Cable Standard – Mini 300 mm »** : 16 mm de large côté caméra, ~12 mm côté Pi 5 (22 broches 0,5 mm). | Canal et fenêtres de 18 mm ; on enfile l'extrémité **Mini** (étroite) depuis la tête vers le pied. |
| **Pi 5 + AI HAT+ (Hailo)** dans un boîtier imprimé noir à fentes d'aération verticales, parois ≈ 3 mm ; la nappe sort par le dessus ; **un couvercle recevra le pied** (décision du 30/09). Sur la photo au mètre-ruban, le connecteur CAM se situe ≈ 35 mm sous le bord du boîtier, le long d'une paroi longue. | Pied « couvercle » à fût décalé (`pied_decal` = 10) : platine affleurant la paroi, trou nappe Ø22 dans le couvercle à 16 mm du bord extérieur ; gabarit de perçage fourni (STL, DXF, SVG). Variante cavalier conservée (`mur_ep` = 3). |

Autres hypothèses : PETG (fluage faible, tenace) ; buse 0,4 ; couches 0,2 (0,15 pour la visserie) ; retrait/élargissement FDM typique de 0,1 à 0,2 mm sur les trous, compensé par les jeux listés au § 9.

---

## 3. Cahier des charges déduit

1. Porter une Camera Module 3 (≈ 4 g) au bout d'un bras d'environ la longueur du câble (300 mm), fixé sur le boîtier du Pi 5.
2. Trois axes de réglage, maintien de la position sans dérive une fois réglé (application fixe de comptage).
3. Nappe protégée sur tout le trajet, sans pliure serrée (rayon statique ≥ 5 à 6 mm), sans traction sur les connecteurs.
4. Le moins de quincaillerie métallique possible ; pièces imprimables sur Prusa (plateau 250 × 210) **sans support**.
5. Montage / démontage à la main (aucun outil, sauf éventuellement une pièce de monnaie pour les vis moletées).
6. Respect des zones sensibles de la caméra : flex autofocus à l'avant, connecteur au dos, champ de vision (66° H × 41° V, 75° diagonal pour le module standard).

---

## 4. Options étudiées et arbitrages

### 4.1 Type d'articulation

| Option | Avantages | Inconvénients | Verdict |
|---|---|---|---|
| Rotule imprimée + collier fendu | 3 axes en une pièce | Fluage du plastique, tenue aléatoire, nappe forcément à l'extérieur | rejetée |
| Charnière à friction plane (boulon traversant) | simple | Le boulon occupe l'axe → la nappe doit contourner l'axe : longueur variable, boucles de réserve, pincement ; tenue dépendante du serrage (fluage) | rejetée |
| Charnière à pions latéraux + friction | axe libre pour la nappe | tenue uniquement par friction | rejetée |
| **Charnière à fenêtre + rosette crantée (24 dents) + vis imprimée** | axe libre pour la nappe, **verrouillage positif**, réglage par pas de 15°, visserie imprimée | 1 vis + 1 écrou par axe, réglage discret (15°) | **retenue** (le pas de 15° est largement suffisant pour cadrer une scène ; l'autofocus et le recadrage logiciel font le reste) |

### 4.2 Passage de la nappe

| Option | Verdict |
|---|---|
| Nappe à l'extérieur, colliers | rejetée : inesthétique, exposée, boucles aux articulations |
| Canal ouvert (U) + clips | possible mais moins protecteur |
| **Canal fermé 18 × 2,4 traversant + fenêtres à l'axe** | **retenue** : on enfile l'extrémité étroite (Mini) ; pont de 18 mm trivial pour la Prusa |

### 4.3 Axe de charnière dans le plan de la nappe ou décalé ?

Un premier passage de conception avec l'axe décalé de 7 mm (pour imprimer le bras d'une pièce à plat) a été **invalidé par le calcul** : au-delà de ~90° de pliage, le point d'entrée du canal côté tête revient vers le point de sortie côté bras et la nappe devrait former une boucle impossible. Avec l'axe **dans** le plan de la nappe, le trajet est un arc tangent aux deux canaux : rayon 11 mm à 90°, 6,4 mm à 120°, longueur quasi constante, et le pliage est possible **des deux côtés** (le bras peut basculer à gauche ou à droite de la tourelle sans changer de pièces).

![Trajet de la nappe](renders/41_schema_trajet_nappe.png)

Conséquence : oreilles symétriques (±11 mm autour de l'axe), donc bras en **deux pièces** pour imprimer sans support (corps à plat, fourches debout).

### 4.4 Fixation de la caméra

| Option | Verdict |
|---|---|
| 4 vis M2 + entretoises | rejetée (métal) |
| Pions Ø2 thermo-rivetés | irréversible |
| **Sandwich coque/façade sur les 4 trous, pions de centrage Ø1,8, façade encliquetée** | **retenue** : démontable, zéro vis |

### 4.5 Fixation sur le boîtier du Pi 5

| Option | Verdict |
|---|---|
| Vissage direct dans le chant d'une paroi de 3 mm | impossible (trop mince) |
| **Platine 4 fentes sur le couvercle**, fût décalé vers le bord, vis M3 ou goupilles imprimées collées, trou Ø22 sous le fût | **retenue** (décision du 30/09) |
| **Adaptateur cavalier** à cheval sur une paroi, 2 trous traversant les fentes d'aération | **fournie en variante** (`01b_cavalier_adaptateur`) |
| Écrou-tenon dans une fente d'aération (boulon imprimé plat) | à étudier une fois la largeur des fentes mesurée |

### 4.6 Matière

**PETG** recommandé (tenue au fluage sous précontrainte, ténacité, surfaces des filets). PLA acceptable pour un prototype de validation des cotes ; ASA/ABS si exposition au soleil derrière une vitre.

---

## 5. Architecture et cinématique

### 5.1 Repères et poses

* Pied : Z vertical, platine en Z = −4…0, fût Ø26 jusqu'à Z = 12,5, tenon Ø24 jusqu'à 15,5, alésage Ø20 traversant.
* Collier-tourelle : Z = 0…12 ; **axe d'épaule** horizontal (Y) à Z = 28, à l'aplomb du fût.
* Bras : X = longueur (entraxe `bras_L` = 150), Y = axes de charnière, Z = épaisseur ; plan de nappe Z = 0.
* Tête : x = largeur PCB, y = hauteur (connecteur en bas), z = profondeur (objectif vers +z) ; axe de tête à 12 mm sous la paroi basse, dans le plan de nappe (z = 4,8).

Angles : **lacet ψ** (rotation du collier), **épaule θ** (0 = bras vertical, 90 = horizontal), **tête β** (0 = tête dans le prolongement du bras, 90 = perpendiculaire, objectif vers l'avant du bras).

### 5.2 Table de visée (élévation de l'axe optique, calculée par le script)

| épaule θ \ tête β | 60° | 90° | 120° | 150° |
|---|---|---|---|---|
| 45° | +75° | +45° | +15° | −15° |
| **60°** | +60° | +30° | **0° (horizontal)** | −30° |
| 90° | +30° | 0° | −30° | −60° |

Règle simple : **élévation = 180° − θ − β**. Pour viser vers le bas (comptage d'un passage vu de haut), on met le bras horizontal (θ = 90) et la tête à 120–135°.

![Pose horizontale](renders/05_pose_horizontal.png)
![Pose repos](renders/05_pose_repos.png)
![Lacet 45°](renders/05_pose_lacet45.png)

### 5.3 Plages et butées

| Axe | Plage sans collision (calculée) | Plage recommandée | Limite physique |
|---|---|---|---|
| Lacet ψ | 360° | ±90° autour de la position neutre | torsion de la nappe sur ≈ 40 mm libres entre la sortie du boîtier Pi et l'épaule |
| Épaule θ | 0 → 100° (5,7 mm³ de contact à 105°) | 0 → 95° | le bloc racine de la fourche touche la bague de retenue au-delà |
| Tête β | 0 → 135° (417 mm³ à 150°) | 0 → 120° | rayon de nappe 6,4 mm à 120°, 4,6 mm à 135° ; face arrière de la tête vers l'évasement de la fourche à 150° |

---

## 6. Détail des sous-ensembles

### 6.1 Articulation « à fenêtre » (commune épaule / tête)

![Coupe de l'articulation](renders/40_schema_coupe_articulation.png)
![Éclaté épaule](renders/06_detail_epaule_eclate.png)

Empilage le long de l'axe (cotes en mm) : fenêtre 18 (nappe 16) → plaque de noix 6 (côté A : poche hexagonale 13,3 profonde 5, fond 1 mm) → écrou-rosette : hexagone 13 × 4,5 dans la poche, flasque conique 45° (imprimable sans support), plat, **24 dents de 1 mm** (r 6,5 → 10) → oreille A 4 mm portant les dents complémentaires sur sa face intérieure, alésage Ø8,6 → tête de vis Ø18 × 5, moletée 12 crans, fente pour pièce de monnaie → filet M8 pas 2 × 11.
Côté B : bossage d'appui Ø16 × 3,5 + tourillon Ø8 × 3,5 dans l'oreille B (Ø8,6), jeu axial 0,5.

Fonctionnement : la vis tire l'écrou-rosette contre l'oreille ; les dents s'emboîtent (pas 15°) ; l'hexagone bloque l'écrou dans la noix ; le couple passe donc noix → hexagone → dents → oreille, **sans dépendre de la friction**. La vis ne supporte que la précontrainte axiale.

Dimensionnement : masse mobile à l'épaule ≈ 55 g (bras ≈ 33 g, tête équipée ≈ 20 g), centre de gravité ≈ 90 mm → couple ≈ **0,05 N·m**. Couple de verrouillage de la rosette ≈ F·r_moyen ≈ 100 N × 8,25 mm ≈ 0,8 N·m pour un serrage à la main modéré (vis M8 pas 2, tête Ø18) : facteur ≥ 10, et encore ≈ 4 avec seulement 30 N résiduels après fluage. Contrainte dans le noyau de vis (Ø6) : < 6 MPa (PETG ≈ 50 MPa). Cisaillement du filet imprimé (4,5 mm engagés) : capacité ≈ 1 kN.

### 6.2 Fourche (× 2, identiques) — embout de bras

![Fourche](renders/20_piece_04b_fourche_x2.png)

Oreilles 4 mm à |Y| = 19…23 (hors tout **46**), rayon 11 ; oreille A crantée, oreille B lisse. Bloc racine 46 × 22 (X = −19…−11) **encoché** au centre (seule la section du corps 24 × 8 subsiste pour |Y| < 16) : c'est ce qui dégage la face arrière de la tête jusqu'à 135°. Évasement loft 30 × 14 → 46 × 22 sur 8 mm, manchon 30 × 14 avec logement 24,4 × 8,4 profond 21 (fond en X = −13), canal 18 × 2,4 jusqu'à la fenêtre (X = −11). Deux trous Ø3,2 pour goupilles imprimées (ou une goutte de cyanoacrylate).
Impression **debout sur l'ouverture du manchon** : oreilles verticales, dents en nervures sur face verticale, alésages horizontaux — aucun surplomb. Hauteur 45 mm, bordure (brim) 5 mm conseillée.

### 6.3 Corps de bras

Barre 24 × 8 × 124 (= `bras_L` − 26), canal 18 × 2,4 débouchant, 2 trous de goupille à 17,5 mm de chaque bout. Imprimé à plat (pont de 18 mm sur toute la longueur : sans souci). Pour un autre entraxe, ne réimprimer que cette pièce (paramètre `bras_L`, ou variable d'environnement `ARM_L`).

### 6.4 Pied, bague, collier-tourelle (lacet)

![Collier](renders/20_piece_03_collier_tourelle.png)

* **Pied couvercle** (`01_pied_couvercle`) : platine 50 × 46 × 4 dont le fût est décalé de 10 mm vers le bord −y (bord de platine à 16 mm de l'axe du fût = rayon du congé) ; 4 fentes 3,4 × 8 en (±19, −8) et (±19, +24) ; fût Ø26 h 12,5 + congé, tenon Ø24 h 3, alésage Ø20 (la nappe de 16 mm y passe à plat et peut se tordre). Pose : bord −y de la platine affleurant la face extérieure de la paroi du boîtier côté connecteur CAM ; **trou Ø22 dans le couvercle** sous le fût, donc à 16 mm du bord extérieur du boîtier, et 4 trous Ø3,4 (ou 2 seulement) aux fentes. Le **gabarit** `01c_gabarit_percage_couvercle` (plaque 1,2 mm au contour de la platine, percée des 5 trous) se pose sur le couvercle pour pointer ; le même motif est fourni en `export/gabarit_couvercle.dxf` et `.svg` pour l'intégrer directement dans la CAO du couvercle.
* **Variante platine centrée** (`01a_pied_plat_centre`) : 46 × 46, fentes en (±17, ±17), pour une surface d'accueil large.
* **Bague de retenue** Ø32 / Ø24,1 × 3 : emmanchée (une goutte de colle) sur le tenon, elle emprisonne axialement le collier (jeu 0,5). Le collier se met en place **avant** la bague.
* **Collier-tourelle** : anneau Ø34 / Ø26,3 × 12, fente 2 mm, deux pattes 8 × 9 × 10 (poche hexagonale d'un côté, passage Ø8,6 de l'autre) serrées par la vis M8 × 20 + écrou hexagonal 13 × 5 ; la noix d'épaule (2 plaques R10, gap 18, col 16) est sur le dessus. Le serrage du collier fige le lacet par friction sur le fût (couple de tenue ≈ 0,4 N·m avec 100 N de serrage, très supérieur aux sollicitations d'une caméra fixe).
* **Adaptateur cavalier** (variante) : platine 46 × 46 × 4 à cheval sur une paroi de `mur_ep` = 3 (+0,4 de jeu) ; joue extérieure 25 mm, intérieure 14 mm (paramètres), 2 trous Ø3,4 pour pincer la paroi à travers les fentes d'aération, 2 trous Ø3,4 recevant le pied plat, passage Ø22 pour la nappe. Imprimé retourné.

### 6.5 Tête caméra

![Tête éclatée](renders/08_tete_eclatee.png)
![Coque intérieur](renders/09_tete_coque_interieur.png)
![Façade intérieur](renders/10_tete_facade_interieur.png)

* **Coque** 31,6 × 30,4, fond 2, logement PCB 25,6 × 24,4 (jeu 0,3/0,27 par côté), 4 plots Ø3,6 h 4 + pions Ø1,8 h 1 aux trous, fente nappe 18 × 2,4 centrée sur z = 4,8 dans la paroi basse, épaulement de jupe 1,2 × 6 et 2 rainures d'encliquetage, noix de charnière (plaques 6 mm à |x| = 9…15, R10, col 12, dépassement arrière 5,2 mm du disque). Imprimée sur sa paroi haute (noix vers le haut).
* **Façade** : jupe 1,2 mm (jeu 0,15) avec 2 crochets 0,6 × 8 (rampe d'entrée, face de retenue plate), plaque avant 1,5 mm, ouverture optique carrée 13 (r 3) centrée sur l'objectif, 4 fûts Ø3,6 descendant jusqu'à la face avant du PCB. L'objectif (8 mm) reste 0,5 mm sous la face intérieure : aucun vignettage (demi-angle diagonal 37,5°, ouverture r ≥ 6,5 à 0,5 mm de l'entrée de pupille).
* **Zones respectées** : flex autofocus (x ∈ ±6, y ∈ 3…10 à l'avant) — la façade ne touche le PCB qu'aux 4 trous ; connecteur dos 20,5 × 5,5 × 3 ; composants dos ≤ 1,5 mm.
* Thermique : IMX708 < 0,5 W ; la coque fermée suffit. Deux fentes latérales optionnelles si usage en plein soleil.

### 6.6 Visserie imprimée

| Pièce | Qté | Détail |
|---|---|---|
| Vis moletée M8 pas 2, L11 | 2 | articulations épaule et tête |
| Vis moletée M8 pas 2, L20 | 1 | collier de lacet |
| Écrou-rosette 24 dents | 2 | hexagone 13 × 4,5, flasque conique, dents 1 mm |
| Écrou hexagonal 13 × 5 | 1 | collier |
| Goupille Ø3 × 7 à tête | 4 | emmanchement corps/fourches (facultatif si collage) |

Filet : profil 60° aplati (crête plate 0,35, fond plat 0,5), profondeur 0,9, noyau Ø6, **jeu radial écrou 0,4** (0,8 sur le diamètre). Le pas de 2 mm est délibérément « gros » : c'est ce qui rend un filet FDM fiable avec une buse 0,4.

**Construction et vérification du filetage** (correction du 30/09, à la suite de ta demande de vérifier la vis). La première version construisait le filet par balayage hélicoïdal du profil puis fusion avec le noyau : OCCT échouait silencieusement sur ce booléen et **les vis livrées étaient des cylindres lisses, les écrous des trous lisses**. La macro construit maintenant la tige filetée par **loft lisse de sections complètes** : chaque section transversale est un polygone de 48 points dont le rayon suit le profil de filet en fonction de l'angle, et la section tourne avec z (12 sections par pas). Noyau et filet forment un seul solide, sans aucun booléen fragile ; la tête est fusionnée avec 1 mm de pénétration, la pointe est conique (réduction des dernières sections). Les écrous sont obtenus par découpe d'une « vis virtuelle » majorée du jeu. Contrôles automatiques dans la macro :

* présence des gorges dans chaque écrou (alternance matière/vide au rayon moyen du filet : 7 transitions sur l'écrou-rosette, 5 sur l'écrou hexagonal) ;
* dans l'assemblage, la vis est tournée sur son axe à la phase qui centre ses crêtes dans les gorges de l'écrou (épaule 180.0°, tête 180.0°, collier 315.0°) ; volume d'interpénétration vis/écrou à cette phase : **0.0 mm³**, distance mini 0.201 mm ;
* preuve d'existence du filet : la même vis tournée d'un demi-tour (décalage d'un demi-pas) pénètre l'écrou de **16.491 mm³**.

![Vérification du filetage](renders/43_verification_filetage.png)

Le lissage B-spline arrondit légèrement les angles du profil et consomme une partie du jeu aux coins : c'est pourquoi le jeu nominal est passé de 0,3 à 0,4 mm. Si l'essai d'impression (vis + écrou, 25 min) tourne trop dur, passer `vis_jeu` à 0,5 ; s'il flotte, revenir à 0,3.

---

## 7. La nappe : trajet, budget, consignes

![Budget nappe](renders/42_budget_nappe.png)

| Tronçon | mm | Statut |
|---|---|---|
| Connecteur CAM du Pi 5 → couvercle (≈ 35 mm mesurés + coude + insertion) | 45 | mesuré sur photo, à confirmer |
| Couvercle → dessous de la platine (platine posée sur le couvercle) | 0 | — |
| Platine → axe d'épaule (fût + collier + col) | 32 | calculé |
| Bras (entraxe) | 150 | paramètre |
| Axe de tête → connecteur CM3 (col + paroi + dos + insertion) | 25,4 | calculé |
| Réserve de courbure aux deux charnières | 6 | calculé |
| **Total** | **258,4** | **marge 41,6 mm** sur 300 (21,6 mm avec le corps de 170) |

Deux corps de bras sont fournis : **150** (marge ≈ 42 mm, recommandé pour la première impression) et **170** (`04a_bras_corps_L170_alt`, marge ≈ 22 mm). Au-delà, passer au câble officiel Standard–Mini **500 mm** (alors `bras_L` jusqu'à ≈ 330, ou deux segments + coude, § 13).

Consignes de montage de la nappe :
1. Enfiler l'extrémité **Mini** (12 mm) depuis la fente de la tête, à travers la fenêtre de tête, le canal du bras, la fenêtre d'épaule, le fût.
2. Contacts orientés comme sur les photos (côté standard : contacts vers le PCB, verrou du connecteur CM3 refermé après insertion complète).
3. Laisser 5 à 10 mm de mou **dans la tête** (entre la fente et le connecteur) et le reste sous la platine ; ne jamais tendre la nappe sur un connecteur.
4. Marquer la position neutre du lacet (trait sur le collier et le fût) : rester dans ±90°.
5. Ne pas plier au-delà de 120° à la tête ni descendre l'épaule sous 95°.

---

## 8. Vérifications effectuées (automatiques, dans la macro)

* **Validité géométrique** : 17 solides `isValid()` = vrai, 1 seul solide par pièce (la façade en produisait 5 avant correction des fûts d'appui).
* **Filetage** (§ 6.6) : gorges présentes dans les deux écrous, interpénétration vis/écrou 0.0 mm³ à la phase alignée contre 16.491 mm³ à un demi-pas de décalage, distance mini 0.201 mm. Ce contrôle a été ajouté après la découverte que la première construction produisait des vis lisses.
* **Concordance des axes** : axe local du bras sur l'axe d'épaule (0, 0, 28) ; écart axe de tête = 0,000 mm.
* **Interférences** (volumes communs, mm³) : 0 pour épaule 0/30/60/90/100°, tête 0/30/60/90/120/135° ; fourche/collier 0 ; fourche/coque 0 ; corps/fourches 0 ; vis/oreilles 0 ; filets vis/écrou 0 (jeu 0,3 confirmé). Valeurs non nulles **attendues** : oreille/écrou-rosette ≈ 5 mm³ (dents modélisées avec 3 % de recouvrement pour la robustesse booléenne), maquette CM3/coque 0,26 mm³ (recouvrement volontaire de 0,01 mm des plots).
* **Rayon de pliage de la nappe** (arc tangent dans la fenêtre de 22 mm) : 41 mm à 30°, 19 à 60°, 11 à 90°, 7,7 à 110°, 6,4 à 120°, 4,6 à 135°.
* **Budget câble** : § 7.
* **Orientation d'impression de la fourche** : vérifiée par assertion (le point le plus bas est l'ouverture du manchon).
* **Coupes axiales de la visserie** : `freecad/verif_filetage_freecad.py` (sous `freecadcmd`) exporte les coupes, `freecad/verif_filetage_figure.py` trace la figure `renders/43_verification_filetage.png`.

Non vérifié (à faire sur pièces réelles) : couple de serrage réel des vis imprimées, tenue au fluage à long terme, cotes FDM de ta machine (§ 9.3).

---

## 9. Impression sur la Prusa

### 9.1 Nomenclature des pièces à imprimer

![Planche](renders/30_planche_impression.png)

| Fichier STL (`export/stl/`) | Qté | Orientation (déjà appliquée dans le STL) | Volume plein | Remarques |
|---|---|---|---|---|
| `01_pied_couvercle` | 1 | platine sur le plateau | ≈ 11 cm³ | fixation sur couvercle |
| `01c_gabarit_percage_couvercle` | 1 | à plat | ≈ 2 cm³ | gabarit de pointage des 5 trous du couvercle |
| `01a_pied_plat_centre` | 0/1 | platine sur le plateau | 10,3 cm³ | variante |
| `01b_cavalier_adaptateur` | 0/1 | retourné (joues en haut) | 13,9 cm³ | variante paroi |
| `02_bague_retenue` | 1 | à plat | 1,0 cm³ | — |
| `03_collier_tourelle` | 1 | debout (anneau sur le plateau) | 10,4 cm³ | brim 5 mm |
| `04a_bras_corps_L150` | 1 | à plat | 18,4 cm³ | pont 18 mm |
| `04a_bras_corps_L170_alt` | 0/1 | à plat | ≈ 21 cm³ | alternative entraxe 170 |
| `04b_fourche_x2` | **2** | debout sur le manchon | 11,4 cm³ | brim 5 mm |
| `04c_goupille_x4` | 4 | tête sur le plateau | 0,1 cm³ | facultatif (colle) |
| `05_tete_coque` | 1 | paroi haute sur le plateau, noix en haut | 8,3 cm³ | — |
| `06_tete_facade` | 1 | face avant sur le plateau | 4,4 cm³ | l'ouverture optique donne une belle face |
| `07_vis_M8_L11_x2` | **2** | tête sur le plateau | 1,5 cm³ | couches 0,15 |
| `08_vis_M8_L20` | 1 | tête sur le plateau | 1,8 cm³ | couches 0,15 |
| `09_ecrou_rosette_x2` | **2** | hexagone sur le plateau, dents en haut | 1,2 cm³ | couches 0,15 |
| `10_ecrou_hex` | 1 | à plat | 0,5 cm³ | couches 0,15 |

Total ≈ 83 cm³ « pleins », soit ≈ 70 à 80 g de PETG une fois remplis à 25 % ; durée totale ≈ 8 à 10 h en 0,2 mm (estimation grossière, à confirmer dans PrusaSlicer). **Aucun support** sur aucune pièce.

### 9.2 Réglages conseillés

* PETG, buse 0,4, couches 0,2 (0,15 pour la visserie et les écrous) ; 3 périmètres (4 pour les fourches et le collier) ; remplissage gyroïde 25 % (100 % pour vis, écrous, goupilles, bague).
* Pas de supports ; brim 5 mm pour les fourches et le collier ; ventilation PETG normale ; température de lit propre à ton filament.
* Ordre conseillé : **d'abord le kit de calibration du filetage** `export/stl/20_kit_calibration_plateau.stl` (≈ 40 min) : une vis L11 et trois écrous-rosette à jeu radial 0,3 / 0,4 / 0,5 mm, marqués 1, 2 et 3 points sur un pan de l'hexagone. On visse chaque écrou à la main : le bon est celui qui s'engage sans forcer et tourne avec deux doigts sans jeu perceptible. Reporter la valeur dans `vis_jeu`, régénérer, puis imprimer le reste. Seuls les écrous dépendent du jeu : les vis définitives peuvent être imprimées dès ce premier essai. Le kit est produit par `freecad/kit_calibration.py`.

![Kit de calibration](renders/44_kit_calibration_filetage.png)

### 9.3 Tolérances et jeux prévus (paramètres)

| Ajustement | Jeu prévu | Paramètre |
|---|---|---|
| Corps de bras dans le manchon de fourche | 0,2 par côté | `manchon_jeu` |
| Collier sur fût | 0,15 par côté (Ø26,3 / Ø26) | `collier_jeu` |
| Bague sur tenon | 0,05 (emmanchement serré) | `bague_jeu` |
| PCB dans la coque | 0,3 / 0,27 par côté | `pcb_jeu_l`, `pcb_jeu_h` |
| Jupe de façade sur épaulement | 0,15 par côté | `jupe_jeu` |
| Hexagone dans les poches | 0,3 | `ecrou_jeu` |
| Filet vis / écrou | 0,4 radial (le lissage B-spline en consomme une partie aux angles) | `vis_jeu` |
| Alésage d'oreille / tourillon Ø8 | 0,3 | `oreille_trou` |

Si ta Prusa imprime « gras » (trous étroits), augmente `vis_jeu` à 0,5 et `collier_jeu` à 0,4, puis régénère (§ 14). Si le collier ne serre pas assez : réduire `collier_jeu` ou élargir `fente_collier`.

---

## 10. Montage pas à pas (aucun outil)

1. **Tête** : poser le PCB dans la coque sur les 4 plots (les pions Ø1,8 entrent dans les trous). Brancher la nappe (extrémité Standard 16 mm) dans le connecteur du dos **avant** de fermer, la faire passer dans la fente basse. Emboîter la façade : clic des 2 crochets.
2. **Bras** : enfiler l'extrémité Mini de la nappe dans la fenêtre de la fourche de tête, le manchon, le corps, la seconde fourche. Emmancher les fourches sur le corps (21 mm), avec les **oreilles crantées (A) du même côté**. Goupilles Ø3 (ou colle).
3. **Charnière de tête** : écarter légèrement les oreilles, engager le tourillon Ø8 de la coque dans l'oreille lisse, glisser l'écrou-rosette dans la poche hexagonale de la noix, dents vers l'oreille crantée, visser la vis L11 de l'extérieur.
4. **Base** : nappe à travers l'alésage du fût, collier enfilé sur le fût (pattes à l'opposé du sens de basculement du bras), bague de retenue emmanchée/collée sur le tenon. Vis L20 + écrou hexagonal dans les pattes, serrage léger.
5. **Charnière d'épaule** : idem étape 3 avec la fourche d'épaule sur la noix du collier.
6. **Fixation** : platine sur le boîtier (2 à 4 points, § 12), nappe branchée sur CAM/DISP 0 du Pi 5 (verrou refermé). Régler lacet → épaule → tête ; resserrer les trois vis à la main ; **resserrer après 24 h** (relaxation du PETG).

Réglage courant : desserrer ½ tour la vis concernée, tourner par crans de 15°, resserrer.

---

## 11. Quincaillerie

| Métal | Par défaut | Option |
|---|---|---|
| Vis M3 pour la platine | **0** (goupilles imprimées collées ou colle) | 2 à 4 × M3 × 8–12 + écrous ou inserts si tu préfères du démontable |
| Autres | **0** | — |

Tout le reste (3 vis, 3 écrous, 4 goupilles, bague) est imprimé.

---

## 12. Points à mesurer / valider avant d'imprimer le tout

1. **Longueur de nappe consommée dans le boîtier Pi** : ≈ 35 mm entre le connecteur CAM et le bord du boîtier d'après la photo au mètre ; à confirmer une fois le couvercle en place. Si > 85 mm : garder le corps de 150, sinon le corps de 170 est possible.
2. **Couvercle** (décision prise) : percer le trou nappe Ø22 à 16 mm du bord extérieur, au-dessus du connecteur CAM, et les 4 trous Ø3,4 avec le gabarit ; vérifier que le couvercle est assez rigide sous la platine (renfort local 2 mm si le couvercle est ajouré).
3. **Sens de basculement souhaité** du bras (le collier se monte pattes à l'opposé) et position neutre du lacet.
4. **Variante de caméra** : standard (objectif 8 mm) ou Wide (9 mm → `objectif_h`).
5. Impression de calibration : 1 vis L11 + 1 écrou-rosette + la bague (30 min).

---

## 13. Évolutions possibles (sans refonte)

* **4ᵉ axe (coude)** : une pièce « noix–noix » (deux noix dos à dos avec un canal de 30 mm) entre deux corps de bras ; les fourches et la visserie existantes conviennent. Nécessite le câble 500 mm.
* **Câble 500 mm** : `bras_L` jusqu'à ≈ 330 mm en un seul segment (vérifier la flèche du corps 24 × 8 : à 330 mm et 20 g en bout, flèche < 1 mm).
* **Rotation de la tête sur elle-même (portrait/paysage)** : coque avec noix tournée de 90° (paramètre à ajouter) ; la fente de nappe devient latérale.
* **Fixation par écrou-tenon dans les fentes d'aération** : boulon plat imprimé glissé dans une fente + écrou à oreilles imprimé : zéro perçage du boîtier.
* **Adaptateur GoPro** : remplacer la noix de la coque par deux « doigts » GoPro pour utiliser des supports du commerce (mais vis M5 métal).
* **Ventilation de la tête** : 2 fentes latérales 1 × 8 si usage derrière une vitre au soleil.

---

## 14. Fichiers livrés et régénération

```
hardware/camera-arm/
├── ETUDE.md                          ← ce document
├── freecad/
│   ├── bras_camera_cm3.py            ← macro FreeCAD paramétrique (dictionnaire P en tête de fichier)
│   ├── render_stl.py                 ← rendus PNG sans OpenGL (rastériseur numpy)
│   ├── make_renders.py               ← série de rendus de l'étude
│   ├── schemas_2d.py                 ← schémas cotés (matplotlib)
│   ├── verif_filetage_freecad.py     ← contrôle de la visserie imprimée (coupes axiales, volumes) sous freecadcmd
│   ├── verif_filetage_figure.py      ← figure 43 à partir des coupes
│   └── kit_calibration.py            ← kit d'essai du jeu de filetage (vis + 3 écrous 0,3/0,4/0,5)
├── export/
│   ├── fcstd/00_assemblage.FCStd     ← toutes les pièces placées (pose par défaut) + feuille « Pose »
│   ├── fcstd/NN_*.FCStd              ← une pièce par document + feuille « Parametres »
│   ├── step/NN_*.step                ← STEP (repère de conception)
│   ├── stl/NN_*.stl                  ← STL orientés pour l'impression, posés en Z = 0
│   ├── gabarit_couvercle.dxf / .svg  ← motif de perçage du couvercle (repère : centre du fût)
│   ├── coupes_filet.json             ← coupes axiales vis / écrous (contrôle du filetage)
│   └── rapport.json                  ← paramètres, volumes, vérifications, budget nappe
└── renders/*.png
```

Régénérer avec d'autres paramètres :

* **Dans FreeCAD (Windows)** : Macro → Macros… → sélectionner `bras_camera_cm3.py` → Exécuter. Éditer d'abord `P = dict(...)` en tête de fichier (ex. `bras_L=130`). Les exports partent dans `%USERPROFILE%\bras_camera_out` (ou le dossier `OUT_DIR`).
* **En ligne de commande** : `OUT_DIR=./export ARM_L=130 freecadcmd -c "exec(open('bras_camera_cm3.py', encoding='utf-8').read())"` (≈ 75 s).
* Rendus : `python3 make_renders.py ./export ./renders` puis `python3 schemas_2d.py ./renders` (dépendances : numpy, pillow, matplotlib).

Le modèle est paramétrique **par le script** (relancer = tout régénérer, y compris les contrôles) ; les `.FCStd` contiennent les solides résultants (`Part::Feature`) et la feuille de paramètres à titre documentaire, pas un arbre PartDesign pilotable à la souris.

**Compatibilité de version** : les `.FCStd` ont été écrits par FreeCAD 26.3 (build conda-forge du 16/09/2026). Un FreeCAD 1.0 ou 1.1 les ouvre normalement (contenu `Part::Feature` + feuille de calcul), au pire avec un avertissement de version ; en cas de refus, importer les `.step` ou rejouer la macro dans ta version, ce qui régénère des fichiers natifs.

---

## 15. Risques et points d'attention

| Risque | Effet | Parade |
|---|---|---|
| Nappe trop courte (tronçons estimés) | impossible de brancher | mesurer (§ 12), `bras_L` ou câble 500 |
| Filet imprimé trop serré / trop lâche | vis bloquée ou écrou qui tourne | impression de calibration ; `vis_jeu` (0,4 nominal, 0,3 à 0,5 selon la machine) |
| Fluage PETG sous précontrainte | perte de serrage | rosette crantée (tenue positive) ; resserrer à 24 h |
| Pliage de tête > 120° | rayon nappe < 6 mm | butée visuelle : ne pas dépasser le cran 8 (120°) |
| Torsion de nappe au lacet | fatigue du polyimide | ±90°, repère sur le collier |
| Pions Ø1,8 fragiles à l'impression | casse au montage | ils ne servent qu'au centrage ; le logement 25,6 × 24,4 positionne déjà le PCB |
| Écrou-rosette qui tombe de la poche au montage | agaçant | léger serrage de l'hexagone (jeu 0,3) ; monter la vis aussitôt |
| Position réelle des connecteurs CAM du Pi 5 | choix du côté de fixation | à relever sur ton boîtier (les deux CAM/DISP sont sur le bord des micro-HDMI) |
