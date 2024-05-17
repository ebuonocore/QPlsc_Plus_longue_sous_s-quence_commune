"""
Définition des classes utilisées lors de la recherche de PLSC
PLSC: Recherhche d'une Plus longue sous-séquence commune entre 2 chaînes

Eric Buonocore. Le 06/06/2021
"""

# ********** Classes **********
class ResoPLSC:
    """ Modélisation de la résolution de la recherche d'une PLSC
    Attributs: X et Y (séquences 1 et 2), tableau des recherches partielles:
    agrégateur des cases du tableau et des flèches
    """

    def __init__(self, x="", y="", cases=[]):
        self.X = x  # Chaîne de la séquence1
        self.Y = y  # Chaîne de la séquence2
        self.tableau = [[]]
        # Agrégateur des cases. Format: (label,(x,y), indice_couleur)
        self.cases = cases
        # Agrégateur des flèches: tableau à 2 dimension. Contient le type de flèche
        self.flèches = []
        # [[liste des ponts de valeur 0], ...[liste des ponts de valeur max(m,n)]]
        self.ponts = []
        self.chemin = None  # Description du bactracking à dessiner en pointillés
        # Format d'une ligne: ((x1, y1),(x2, y2))
        self.chemins =  []  # Liste des chemins possibles
        self.couleurs = {'neutre': (200, 200, 200), 'base': (80, 80, 255),
                         'alerte': (224, 0, 0),  'message': (230, 230, 0),
                         'actif': (0, 192, 0)}

    def backtracking_mem(self, i:int, j:int, valeur:int, branches:list)->list:
        """ Initialise le dictionnaire de mémoïsation et lance la retour sur
        trace récursif.
        """
        dicto_memo = dict()
        def backtracking_rec(i:int, j:int, valeur:int, branches:list)->list:
            """ A partir du tableau des recherches partielles et de X et Y
            retrouve récursivement tous chemins menant aux PLSC
            Renvoie la liste des différents chemins : Liste de listes de tuples
            (i,j) est le point de départ du pont précédent, valeur est la
            valeur de cette case.
            """
            if (i, j) in dicto_memo:
                return dicto_memo[(i, j)]
            # Cas de base: Plus de pont à ce niveau, renvoie une liste de liste vide
            if valeur == 0:
                return [[(i+1, j+1)]]
            # Initialise la liste des chemins
            pistes = []
            # Test les ponts valides depuis ce point d'entrée (i,j)
            for pont in self.ponts[valeur]:
                if pont[0] <= i and pont[1] <= j:
                    # Pour chaque pont valide, récupère la liste des chemins possibles
                    branches = backtracking_rec(pont[0]-1, pont[1]-1,
                                                valeur-1, branches)
                    # Reconstruit une liste unique de tous les chemins possibles
                    # précédés par le pont
                    for branche in branches:
                        pistes.append([(i+1, j+1)] + branche)
            dicto_memo[(i, j)] = pistes
            return pistes
        return backtracking_rec(i, j, valeur, branches)

    def  chemin_vers_chaîne(self, chemin_sélection):
        """ Renvoie la chaîne correspondante à un chemin
        """
        if chemin_sélection>=len(self.chemins):
            return ""
        chaînePlsc = ""
        # La première coordonnée du chemin correspond au point (len(self.X), len(self.Y))
        # hors du tableau: On n'en tient pas compte dans la résolution du problème
        chemin = self.chemins[chemin_sélection][1:]
        for case in chemin:
            caractère = self.X[case[0]]
            chaînePlsc = caractère + chaînePlsc
        return chaînePlsc

    def cherche_case(self, x: int, y: int):
        """ Parcours toutes les cases à la recherche de la case d'abscisse x
        et d'ordonnée y
        Renvoie None s'il ne la trouve pas.
        """
        for case in self.cases:
            if case.x == x and case.y == y:
                return case
        return None


class Cases:
    """ Décrit chaque case du tableau de mémoïsation (avec descripteurs)
    """

    def __init__(self, label, x=0, y=0, couleur=0):
        self.label = label
        self.x = x
        self.y = y
        self.couleur = couleur

    def param(self):
        """ Renvoie les valeurs des attributs de l'instance
        """
        return (self.label, self.x, self.y, self.couleur)
