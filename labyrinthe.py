"""
INF5183 - Résolution d'un labyrinthe par recherche (largeur, profondeur, coût uniforme)
et production d'images en couleur, comme dans la démonstration CS50 AI.

Même méthode que le cours :
  - Q : la frontière, une liste de CHEMINS (chaque chemin = liste d'états)
  - E : l'ensemble des états explorés (déjà étendus)
  - on n'ajoute un voisin v que si v ∉ E ∪ π ∪ États(Q)

Un état est une case (ligne, colonne) du labyrinthe.

Utilisation :
    python labyrinthe.py                      # labyrinthe de l'exemple, largeur
    python labyrinthe.py profondeur           # même labyrinthe, profondeur
    python labyrinthe.py cout                 # coût uniforme
    python labyrinthe.py largeur mon_laby.txt # votre propre labyrinthe

Format d'un fichier labyrinthe (texte) :
    #  mur          A  départ        B  objectif
    espace ou .  case libre (coût 1)
    ~  boue (case libre de coût 5, utile pour voir le coût uniforme travailler)

Sorties (dans le dossier courant) :
    <strategie>.png  image finale : murs, cases explorées, solution
    <strategie>.gif  animation de l'exploration, boucle par boucle

Nécessite Pillow :  pip install pillow
"""

import os
import sys
import webbrowser
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# Labyrinthe de l'exemple (reproduit d'après l'image de la démonstration)
# --------------------------------------------------------------------------
LABYRINTHE_EXEMPLE = """\
 # # ###  #B
 # #   # ##
   # #   ##
# ## # # ##
#    # #
### ## #####
A   ##
"""

# --------------------------------------------------------------------------
# Couleurs (proches de l'image)
# --------------------------------------------------------------------------
COULEURS = {
    "mur":      (40, 70, 120),    # bleu foncé
    "libre":    (15, 15, 15),     # noir : case libre jamais explorée
    "explore":  (200, 225, 150),  # vert pâle : état dans E
    "frontiere":(240, 200, 120),  # orange pâle : état encore dans Q
    "solution": (245, 220, 70),   # jaune : chemin trouvé
    "boue":     (120, 90, 60),    # brun : case de coût 5
    "depart":   (200, 60, 40),    # rouge : A
    "objectif": (40, 160, 70),    # vert : B
    "grille":   (90, 110, 140),
}


# --------------------------------------------------------------------------
# 1. Lire le labyrinthe et le transformer en graphe
# --------------------------------------------------------------------------
def lire_labyrinthe(texte):
    lignes = texte.splitlines()
    largeur = max(len(l) for l in lignes)
    lignes = [l.ljust(largeur) for l in lignes]       # compléter les lignes courtes
    murs, couts = set(), {}
    depart = objectif = None
    for i, ligne in enumerate(lignes):
        for j, car in enumerate(ligne):
            if car == "#":
                murs.add((i, j))
            elif car == "A":
                depart = (i, j)
            elif car == "B":
                objectif = (i, j)
            couts[(i, j)] = 5 if car == "~" else 1
    if depart is None or objectif is None:
        raise ValueError("Le labyrinthe doit contenir un A (départ) et un B (objectif).")
    return lignes, murs, couts, depart, objectif


def voisins(etat_u, murs, hauteur, largeur):
    """Cases libres accessibles en un pas. Ordre fixe : haut, bas, gauche, droite."""
    i, j = etat_u
    candidats = [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]
    return [(a, b) for (a, b) in candidats
            if 0 <= a < hauteur and 0 <= b < largeur and (a, b) not in murs]


# --------------------------------------------------------------------------
# 2. Fonctions du cours
# --------------------------------------------------------------------------
def etat(pi):
    return pi[-1]                      # dernier état du chemin


def etats(Q):
    return {c[-1] for c in Q}          # ensemble des états de la frontière


def pop_min(Q):
    """Retire de Q le (coût, chemin) de coût minimal ; à égalité, le plus ancien."""
    i_min, c_min = 0, Q[0][0]
    for i, (c, _) in enumerate(Q):
        if c < c_min:
            i_min, c_min = i, c
    return Q.pop(i_min)


# --------------------------------------------------------------------------
# 3. Recherche simple : largeur ou profondeur
#    Renvoie le chemin et la liste des "photos" (E et États(Q) à chaque boucle)
# --------------------------------------------------------------------------
def recherche_simple(murs, hauteur, largeur, depart, objectif, strategie):
    Q = [[depart]]                     # étape 1 : initialisation
    E = set()
    photos = []                        # pour l'animation
    while Q:                           # étape 2 : boucle
        if strategie == "largeur":
            pi = Q.pop(0)              # FIFO : le premier chemin
        else:
            pi = Q.pop()               # LIFO : le dernier chemin
        u = etat(pi)
        if u == objectif:              # 2.1 test d'objectif à la SORTIE
            photos.append((set(E), etats(Q), pi))
            return pi, E, photos
        E.add(u)
        for v in voisins(u, murs, hauteur, largeur):          # 2.2 étendre
            if (v not in E) and (v not in pi) and (v not in etats(Q)):
                Q.append(pi + [v])
        photos.append((set(E), etats(Q), None))
    return None, E, photos             # Q vide : aucun chemin


# --------------------------------------------------------------------------
# 4. Coût uniforme avec table d (best) des meilleurs coûts connus
#    Le coût d'un pas = coût de la case d'arrivée (1, ou 5 pour la boue)
# --------------------------------------------------------------------------
def recherche_cout_uniforme(murs, couts, hauteur, largeur, depart, objectif):
    Q = [(0, [depart])]
    best = {depart: 0}
    E = set()
    photos = []
    while Q:
        c, pi = pop_min(Q)
        u = etat(pi)
        if c > best.get(u, float("inf")):
            continue                   # chemin obsolète : on l'ignore
        if u == objectif:
            photos.append((set(E), {p[-1] for _, p in Q}, pi))
            return pi, c, E, photos
        E.add(u)
        for v in voisins(u, murs, hauteur, largeur):
            nv = c + couts[v]
            if (v not in pi) and (nv < best.get(v, float("inf"))):
                best[v] = nv
                Q.append((nv, pi + [v]))
        photos.append((set(E), {p[-1] for _, p in Q}, None))
    return None, float("inf"), E, photos


# --------------------------------------------------------------------------
# 5. Dessin
# --------------------------------------------------------------------------
TAILLE = 50  # pixels par case
BORD = 2
try:
    POLICE = ImageFont.load_default(size=24)   # Pillow 10.1 ou plus récent
except TypeError:
    POLICE = ImageFont.load_default()


def dessiner(lignes, murs, couts, depart, objectif, explores, frontiere, solution):
    hauteur, largeur = len(lignes), len(lignes[0])
    img = Image.new("RGB", (largeur * TAILLE, hauteur * TAILLE), COULEURS["grille"])
    d = ImageDraw.Draw(img)
    chemin = set(solution) if solution else set()
    for i in range(hauteur):
        for j in range(largeur):
            case = (i, j)
            if case in murs:
                coul = COULEURS["mur"]
            elif case == depart:
                coul = COULEURS["depart"]
            elif case == objectif:
                coul = COULEURS["objectif"]
            elif case in chemin:
                coul = COULEURS["solution"]
            elif case in explores:
                coul = COULEURS["explore"]
            elif case in frontiere:
                coul = COULEURS["frontiere"]
            elif couts[case] > 1:
                coul = COULEURS["boue"]
            else:
                coul = COULEURS["libre"]
            x, y = j * TAILLE, i * TAILLE
            d.rectangle([x + BORD, y + BORD, x + TAILLE - BORD, y + TAILLE - BORD], fill=coul)
            if case in (depart, objectif):
                lettre = "A" if case == depart else "B"
                d.text((x + TAILLE // 2, y + TAILLE // 2), lettre, fill="white",
                       font=POLICE, anchor="mm")
    return img


# --------------------------------------------------------------------------
# 6. Programme principal
# --------------------------------------------------------------------------
def main(strategie="largeur", fichier=None, afficher=True):
    """Lance la recherche et produit <strategie>.png et <strategie>.gif.

    Depuis Jupyter ou Spyder, appelez directement, par exemple :
        main("profondeur")
        main("cout", "labyrinthe_boue.txt")
    """
    if strategie not in ("largeur", "profondeur", "cout"):
        raise ValueError("Stratégie inconnue : choisir largeur, profondeur ou cout.")
    if fichier:
        with open(fichier, encoding="utf-8") as f:
            texte = f.read()
    else:
        texte = LABYRINTHE_EXEMPLE

    lignes, murs, couts, depart, objectif = lire_labyrinthe(texte)
    hauteur, largeur = len(lignes), len(lignes[0])

    if strategie == "cout":
        solution, cout, E, photos = recherche_cout_uniforme(
            murs, couts, hauteur, largeur, depart, objectif)
    else:
        solution, E, photos = recherche_simple(
            murs, hauteur, largeur, depart, objectif, strategie)
        cout = sum(couts[c] for c in solution[1:]) if solution else float("inf")

    # Résultats texte
    print(f"Stratégie : {strategie}")
    print(f"États explorés (taille de E) : {len(E)}")
    if solution:
        print(f"Chemin trouvé : {len(solution) - 1} pas, coût {cout}")
        print("Chemin :", " -> ".join(f"({i},{j})" for i, j in solution))
    else:
        print("Échec : aucun chemin.")

    # Image finale
    final = dessiner(lignes, murs, couts, depart, objectif, E, set(), solution)
    final.save(f"{strategie}.png")

    # Animation : une image par boucle, puis l'image finale affichée plus longtemps
    images = [dessiner(lignes, murs, couts, depart, objectif, e, f, None) for e, f, _ in photos]
    images.append(final)
    durees = [150] * (len(images) - 1) + [2500]
    images[0].save(f"{strategie}.gif", save_all=True, append_images=images[1:],
                   duration=durees, loop=0)
    chemin_gif = os.path.abspath(f"{strategie}.gif")
    print(f"Images enregistrées : {os.path.abspath(strategie + '.png')}")
    print(f"                      {chemin_gif}")
    if afficher:
        afficher_animation(chemin_gif)


def afficher_animation(chemin_gif):
    """Affiche le GIF : dans le notebook (Jupyter), sinon dans le navigateur."""
    try:
        from IPython import get_ipython
        from IPython.display import Image as IPyImage, display
        ip = get_ipython()
        if ip is not None and "ZMQ" in type(ip).__name__:    # Jupyter ou Spyder
            with open(chemin_gif, "rb") as f:
                display(IPyImage(data=f.read(), format="gif"))
            return
    except ImportError:
        pass
    webbrowser.open("file://" + chemin_gif)                 # terminal : navigateur


if __name__ == "__main__":
    # En ligne de commande : python labyrinthe.py [strategie] [fichier]
    # Jupyter et Spyder ajoutent leurs propres arguments (ex. "-f ...json") :
    # on ne garde que ceux qui ont du sens pour ce programme.
    args = [a for a in sys.argv[1:] if not a.startswith("-") and not a.endswith(".json")]
    strategie = args[0] if args and args[0] in ("largeur", "profondeur", "cout") else "largeur"
    fichier = args[1] if len(args) > 1 else None
    main(strategie, fichier)
