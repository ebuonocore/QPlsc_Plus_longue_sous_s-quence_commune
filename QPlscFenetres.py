# coding: utf-8
"""
Recherche d'une Plus longue sous-sequence commune entre 2 chaînes (PLSC)
Eric Buonocore. Le 03/06/2021
"""

# ********** Bibliothèques **********
# Bibliothèques qtpy pour les graphiques
from qtpy import QtGui
from qtpy.QtWidgets import (QLabel, QWidget, QHBoxLayout)
from qtpy.QtWidgets import (QMainWindow, QDesktopWidget, QVBoxLayout)
from qtpy.QtWidgets import (QPushButton, QSpinBox, QTextEdit, QCheckBox)
from qtpy.QtWidgets import QFileDialog
from qtpy.QtGui import QPainter, QColor, QPixmap, QImage
from qtpy.QtCore import QRect, Qt, QBuffer, QIODevice
# Système et gestion du temps
import sys
from time import sleep
import io
# Creation des classes ResoPLSC et Cases
from QPlscStructures import Cases, ResoPLSC

from PIL import Image  # Pour la sauvegarde d'images animees
# https://note.nkmk.me/en/python-pillow-gif/


# ********** Classes **********
class ZoneDessin(QWidget):
    """ZoneDessin construit le widget qui accueille le dessin
    Programmation evenementielle: Lors de l'appel de la methode repaint(),
    les elements memorises dans l'objet reso sont redessines
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Echelle du dessin, recalculee lors de l'appel à self.paint()
        self.echelleDessin = 30
        self.marge = 0.2
        self.reso = ResoPLSC()
        # Definit une couleur de fond blanche
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(palette)
        # Definition des images (flèches)
        self.flèche_verte = QPixmap()
        self.flèche_verte_mini = QPixmap()
        self.flèche_vertgris = QPixmap()
        self.flèche_vertgris_mini = QPixmap()
        self.flèche_rouge = QPixmap()
        self.flèche_rouge_mini = QPixmap()

    def dessine_tableau(self, p: QPainter):
        """ Definition de toutes les etapes du dessin dans le QPainter
        """
        ech = self.echelleDessin
        min_ech = int(2*ech//3)
        # Mise à jour de la taille d'ecriture des lettres
        font = QtGui.QFont()
        font.setPointSize(max(1, min_ech))
        p.setFont(font)
        # Parcours la totalite des cases de reso pour les dessiner
        for case in self.reso.cases:
            if case.visible:
                # Recupère les paramètres de dessin des cases
                label, case_x, case_y, col = case.param()
                # Calcul les coordonnees en pixels (x et y) à partir de
                # l'echelle et de la postion de la case dans le tableau
                x = self.indice_vers_pixels(case_x)
                y = self.indice_vers_pixels(case_y)
                # Paramètre le stylo
                color = QtGui.QColor(col[0], col[1], col[2])
                p.setBrush(
                    QColor((col[0]+255)//2, (col[1]+255)//2, (col[2]+255)//2))
                pen = QtGui.QPen(color, 4)
                p.setPen(pen)
                # Dessine le rectangle à bord arrondis
                m = int(ech//10)  # marges
                p.drawRoundedRect(int(x+m), int(y+m), int(ech-m),
                                  int(ech-m), ech//10, ech//10)
                # Change les paramètres du stylo pour ecrire la lettre
                color = QtGui.QColor(col[0]//2, col[1]//2, col[2]//2)
                pen = QtGui.QPen(color, 4)
                p.setPen(pen)
                # La lettre n'est pas écrite si elle est illisble (trop petite)
                if ech >= 12:
                    recText = QRect(int(x), int(y), int(ech), int(ech))
                    p.drawText(recText, 0x84, label)
        # Dessine les portions de chemins retraçant les backtrackings
        if self.reso.chemin is not None:
            col = self.reso.couleurs['actif']
            color = QtGui.QColor(col[0], col[1], col[2])
            p.setBrush(
                QColor((col[0]+255)//2, (col[1]+255)//2, (col[2]+255)//2))
            pen = QtGui.QPen(color, ech//10, Qt.DashDotLine)
            p.setPen(pen)
            for chemin in self.reso.chemin:
                x1 = int(self.indice_vers_pixels(chemin[0][0]) + ech//2)
                y1 = int(self.indice_vers_pixels(chemin[0][1]) + ech//2)
                x2 = int(self.indice_vers_pixels(chemin[1][0]) + ech//2)
                y2 = int(self.indice_vers_pixels(chemin[1][1]) + ech//2)
                p.drawLine(x1, y1, x2, y2)
        # Dessine les flèches
        for j in range(len(self.reso.tableau)):
            for i in range(len(self.reso.tableau[0])):
                x = int(self.indice_vers_pixels(i) - ech//3)
                y = int(self.indice_vers_pixels(j) - ech//3)
                if self.reso.flèches[j][i] == 'vert_actif':
                    p.drawPixmap(x, y, self.flèche_verte_mini)
                if self.reso.flèches[j][i] == 'vert_passif':
                    p.drawPixmap(x, y, self.flèche_vertgris_mini)
                if self.reso.flèches[j][i] == 'rouge_max':
                    p.drawPixmap(x, y, self.flèche_rouge_mini)

    def indice_vers_pixels(self, indice: int) -> int:
        """ Prend l'indice d'une position dans le tableau et le traduit en
        position ecran (pixel) en fonction de l'attribut self.echelleDessin
        """
        echelle = self.echelleDessin
        return echelle*self.marge//2 + (indice+1) * echelle

    def paintEvent(self, event):
        """ Lance le dessin des differents objets (flèches, cases, lignes)
        dans la zone de dessin
        """
        p = QPainter()
        p.begin(self)
        self.dessine_tableau(p)
        p.end()


class Fenetre(QMainWindow):
    """Fenêtre graphique principale.
    Elle contient widgetP qui sera affiche, constitue d'un layout horizontal
    (zoneP) contenant, à gauche le dessin et à droite, widgetD, la structure
    des boutons, cases et spinbox...
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dessin = ZoneDessin()
        # Inidque si la destinaion est un dessin ou une exportation vers un fichier
        self.destinationFichier = False
        self.genère_animation = False  # Image unique ou animation
        # Liste des images de l'animation
        self.images = []  # L'image d'indice 0 est une image vierge, transparente
        self.setWindowTitle("PLSC")

        self.widgetP = QWidget()  # Widget principal
        self.zoneP = QHBoxLayout()  # Cadre principal
        self.widgetD = QWidget()  # Widget droit
        self.colonneD = QVBoxLayout()  # Cadre droit pour widgetD
        # Elements de la partie 'Parametrages'
        self.labelSeq1 = QLabel('Séquence1')
        self.seq1 = QTextEdit()
        self.labelSeq2 = QLabel('Séquence2')
        self.seq2 = QTextEdit()
        self.boxInitialisation = QCheckBox('Initialisation du tableau')
        self.boxInitialisation.setTristate(False)
        self.boxInitialisation.stateChanged.connect(self.recherche_plsc)
        self.completion = QWidget()  # Widget contenant la ligne ligneCompletion
        # Ligne de parametrage de la completion du tableau
        self.ligneCompletion = QHBoxLayout()
        self.boxCompletion = QCheckBox('Complétion du tableau')
        self.boxCompletion.setTristate(False)
        self.boxCompletion.stateChanged.connect(self.recherche_plsc)
        self.labelCompletion = QLabel('Durée animation')
        self.spinCompletion = QSpinBox()  # Selection de la duree de l'animation
        self.labelPlsc = QLabel('PLSC')
        self.boxSelectionUnePlsc = QCheckBox(
            'Une seule')  # Selection d'une seule solution
        self.boxSelectionUnePlsc.setTristate(False)
        self.boxSelectionUnePlsc.stateChanged.connect(self.selection_Plsc_Une)
        self.selectionPlsc = QWidget()  # Widget contenant la ligne ligneCompletion
        # Ligne de parametrage de la completion du tableau
        self.ligneSelectionPlsc = QHBoxLayout()
        self.boxSelectionToutesPlsc = QCheckBox('Toutes')
        self.boxSelectionToutesPlsc.setTristate(False)
        self.boxSelectionToutesPlsc.stateChanged.connect(
            self.selection_Plsc_Toutes)
        self.spinSelectionPlsc = QSpinBox()  # Selection de la duree de l'animation
        self.spinSelectionPlsc.valueChanged.connect(self.mise_a_jour_chemin)
        self.labelSolution = QLabel('Solution')
        self.reponse = QTextEdit()
        # Elements de la partie 'Exportation
        self.labelExport = QLabel('Dimension de l\'exportation:')
        self.labelExportLargeur = QLabel('L')
        self.spinExportLargeur = QSpinBox()
        self.labelExportHauteur = QLabel('H')
        self.spinExportHauteur = QSpinBox()
        self.Export = QWidget()
        self.ligneExport = QHBoxLayout()  # Ligne des paramètres de l'exportation
        self.buttonImage = QPushButton('Exporter de l\'image')
        self.buttonImage.clicked.connect(self.capture_image)
        self.buttonAnimation = QPushButton('Exporter l\'animation')
        self.buttonAnimation.clicked.connect(self.capture_animation)
        self.buttonQuit = QPushButton('Quitter')
        self.buttonQuit.clicked.connect(sys.exit)
        dim = self.taille_ecran()

        # Imbrication des objets
        self.colonneD.addWidget(self.labelSeq1)
        self.colonneD.addWidget(self.seq1)
        self.colonneD.addWidget(self.labelSeq2)
        self.colonneD.addWidget(self.seq2)
        # Case à cocher pour valider l'animation
        self.colonneD.addWidget(self.boxInitialisation)
        self.colonneD.addWidget(self.boxCompletion)
        self.ligneCompletion.addWidget(self.labelCompletion)
        self.ligneCompletion.addWidget(self.spinCompletion)
        self.spinCompletion.setMinimum(0)  # Parametrage de l'animation
        self.spinCompletion.setValue(3)
        self.completion.setLayout(self.ligneCompletion)
        self.colonneD.addWidget(self.completion)
        self.colonneD.addWidget(self.labelPlsc)
        self.colonneD.addWidget(self.boxSelectionUnePlsc)

        self.ligneSelectionPlsc.addWidget(self.boxSelectionToutesPlsc)
        self.ligneSelectionPlsc.addWidget(self.spinSelectionPlsc)
        self.selectionPlsc.setLayout(self.ligneSelectionPlsc)
        self.colonneD.addWidget(self.selectionPlsc)

        self.colonneD.addWidget(self.labelSolution)
        self.colonneD.addWidget(self.reponse)
        self.reponse.setFixedHeight(40)
        # Partie Exportation
        self.colonneD.addWidget(self.labelExport)
        self.ligneExport.addWidget(self.labelExportLargeur)
        self.ligneExport.addWidget(self.spinExportLargeur)
        self.spinExportLargeur.setRange(100, 2000)
        self.spinExportLargeur.setValue(600)
        self.ligneExport.addWidget(self.labelExportHauteur)
        self.ligneExport.addWidget(self.spinExportHauteur)
        self.spinExportHauteur.setRange(100, 1400)
        self.spinExportHauteur.setValue(400)
        self.Export.setLayout(self.ligneExport)
        self.colonneD.addWidget(self.Export)

        self.colonneD.addWidget(self.buttonImage)
        self.colonneD.addWidget(self.buttonAnimation)
        self.colonneD.addWidget(self.buttonQuit)
        self.widgetD.setLayout(self.colonneD)
        self.widgetD.setMaximumWidth(200)
        self.zoneP.addWidget(self.dessin)
        self.zoneP.addWidget(self.widgetD)
        self.widgetP.setLayout(self.zoneP)
        self.widgetP.setGeometry(25, 40, dim[0], dim[1])

    def calculEchelle(self, largeur, hauteur) -> tuple:
        """ A partir de la taille de la zone de dessin ou des paramètres de 
        la sauvegarde souhaitee, met à jour self.dessin.echelleDessin
        Renvoie en pixels la largeur et la hauteur reelles de l'image produite
        """
        D = self.dessin
        T = self.dessin.reso
        # Largeur de la fenêtre / nombre de lignes plus marges
        h_max = hauteur // (len(T.Y) + 1 + D.marge*2)
        l_max = largeur // (len(T.X) + 1 + D.marge*2)
        ech = min(h_max, l_max)
        D.echelleDessin = ech
        largeurReelle = int((len(T.X) + 1 + D.marge*2) * ech)
        hauteurReelle = int((len(T.Y) + 1 + D.marge*2) * ech)
        return largeurReelle, hauteurReelle

    def capture(self):
        """ Déclenhé par le bouton 'Capture'
        Genère le fichier image (ou l'animation si la case est cochée)
        Ouvre la boîte de dialogue pour selectionner le fichier de destination
        """
        # Initialisation des variables
        self.destinationFichier = True
        self.initialisation()
        duree = self.temps_par_image() * 1000
        # MAJ de l'echelle specifique pour la sauvegarde
        largeur, hauteur = self.calculEchelle(self.spinExportLargeur.value(),
                                              self.spinExportHauteur.value())
        # Redimensionnement des flèches à partir des flèches d'origines
        self.redimensionne_flèches()
        # Initialisation de l'image vierge à l'indice 0
        self.initialise_image_vierge(largeur, hauteur)
        # Rafraîchissement de l'affichage à l'ecran et MAJ des instances
        self.dessine_nouvelle_image()
        self.recherche_plsc()
        # Selection du chemin et fichier  pour l'enregistrement
        chemin, extension = QFileDialog.getSaveFileName(self, "Enregistrer l'image", "",
                                                        "Images (*.png *.apng *.gif)")
        # Si la saisie est vide, alors termine l'appel de la fonction
        if chemin == "":
            return
        # Sauvegarde de l'image
        # Consreve l'extension si elle a ete renseignee. Sinon, force le format
        # self.images[0] contient l'image vierge
        # self.images[1] contient la phase d'initialisation
        if self.genère_animation == False:  # S'il s'agit d'une image fixe
            if '.' not in chemin:
                chemin += ".png"  # Format png pour les images fixes
            self.images[-1].save(chemin)
        else:  # S'il s'agit d'une animation.
            if '.' not in chemin:
                chemin += ".gif"  # Format gif pour les animations
            imagesGif = conversion_QImages_vers_GIF(self.images)
            imagesGif[1].save(chemin,
                              save_all=True, append_images=imagesGif[1:], optimize=False, duration=duree, loop=0)
        self.genère_animation = False
        self.destinationFichier = False

    def capture_animation(self):
        """ Lancé lors de l'appui  sur le bouton 'Exporation de l'animation'
        """
        self.genère_animation = True
        self.capture()

    def capture_image(self):
        """ Lancé lors de l'appui  sur le bouton 'Exporation de l'animation'
        """
        self.genère_animation = False
        self.capture()

    def dessine_nouvelle_image(self):
        """ Produit une nouvelle image à partir des nouveaux paramètres du dessin
            L'ajoute à la liste des images: self.images
        """
        D = self.dessin
        # Genère une nouvelle image à partir de l'image vierge
        image = self.images[0].copy()
        p = QPainter()
        p.begin(image)
        D.dessine_tableau(p)
        p.end()
        self.images.append(image)

    def dessine_trace(self, _piste: list):
        """ Dessine le parcours du retour sur trace (backtracking)
        _piste est une liste des tuples des coordonnees des points des
        caractères de la PLSC selectionnee.
        Repasse en vert les caractères selectionnes sur X et Y.
        Construit un chemin en pointilles reliant les ponts
        Passe en vert clair les ponts actifs
        """
        T = self.dessin.reso
        # Initialisation du chemin
        T.chemin = []
        point_origine = (len(T.X)-1, len(T.Y)-1)
        # Initialise toutes les flèches: Soit effacees, soit passees en 'vert_passif'
        # selon la case self.boxSelectionToutesPlsc
        for ponts_valeur in T.ponts:
            for pont in ponts_valeur:
                if self.boxSelectionToutesPlsc.isChecked():
                    T.flèches[pont[1]][pont[0]] = 'vert_passif'
                else:
                    T.flèches[pont[1]][pont[0]] = None
        couleur_ref = 'actif'
        for i in range(1, len(_piste)):
            point_destination = _piste[i]
            x_origine = point_origine[0]
            y_origine = point_origine[1]
            x_destination = point_destination[0]
            y_destination = point_destination[1]
            case_active_X = T.cherche_case(-1, y_destination)
            case_active_Y = T.cherche_case(x_destination, -1)
            case_active_X.couleur = T.couleurs[couleur_ref]
            case_active_Y.couleur = T.couleurs[couleur_ref]
            T.chemin.append(
                ((x_origine, y_origine), (x_destination, y_origine)))
            T.chemin.append(((x_destination, y_origine),
                            (x_destination, y_destination)))
            T.chemin.append(((x_destination, y_destination),
                            (x_destination-1, y_destination-1)))
            # Les ponts sur le chemin de la PLSC passent en clair
            T.flèches[y_destination][x_destination] = 'vert_actif'
            point_origine = (x_destination-1, y_destination-1)

    def efface_traces(self):
        """ Repasse tous les caractères de X et Y en couleur de 'base'
            Initialise le tableau des flèches
        """
        T = self.dessin.reso
        # Remets les marges en bleu
        for x in range(len(T.X)):
            case_active_X = T.cherche_case(x, -1)
            case_active_X.couleur = T.couleurs['base']
        for y in range(len(T.Y)):
            case_active_Y = T.cherche_case(-1, y)
            case_active_Y.couleur = T.couleurs['base']
        # Efface toutes les flèches
        m = len(T.X)
        n = len(T.Y)
        # Cree et initialise le tableau des flèches (m*n) cases
        T.flèches = [[None]*(m) for _ in range(n)]

    def initialisation(self):
        """ Lance l'initialisation du tableau de recherche:
        Creation des axes et première ligne et première colonne
        """
        D = self.dessin
        self.initialise_axes()
        # Mise à jour de l'échelle et de la dimension de la zone utile
        if self.destinationFichier:
            largeur, hauteur = self.calculEchelle(self.spinExportLargeur.value(),
                                                  self.spinExportHauteur.value())
        else:
            largeurDessin = D.size().width()
            hauteurDessin = D.size().height()
            largeur, hauteur = self.calculEchelle(largeurDessin, hauteurDessin)
        self.initialise_image_vierge(largeur, hauteur)
        # Initialise le reste du tableau
        self.reponse.setPlainText("")  # Vide la zone de texte de reponse
        T = self.dessin.reso
        m = len(T.X)
        n = len(T.Y)
        # Cree et initialise le tableau des flèches (m*n) cases
        T.flèches = [[None]*(m) for _ in range(n)]
        # Cree et initialise le tableau des valeurs (m*n) cases
        T.tableau = [[0]*(m) for _ in range(n)]
        # Cree et initialise le tableau des ponts (cases (i, j) verifiant X[i] = Y[j])
        # La PLSC est forcement plus petite que la plus petite sequence
        valeur_max = min(m, n)
        T.ponts = [[] for _ in range(valeur_max)]
        # Initialise la première ligne et la première colonne à 0
        visible = self.boxInitialisation.isChecked()
        for i in range(len(T.X)):
            c = Cases('0', i, 0, T.couleurs['neutre'], visible)
            T.cases.append(c)
            T.tableau[0][i] = 0
        for j in range(len(T.Y)):
            c = Cases('0', 0, j, T.couleurs['neutre'], visible)
            T.cases.append(c)
            T.tableau[j][0] = 0
        # Lance la mise à jour des elements à dessiner (Cases et flèches)
        if self.boxInitialisation:
            self.dessin.repaint()
            self.dessine_nouvelle_image()

    def initialise_axes(self):
        """ Remise à zero des cases et création/initialisation du tableau de recherche.
        Genère les cases des axes créés à partir des séquences saisies dans les
        zones de texte
        """
        T = self.dessin.reso
        T.cases = []
        T.chemin = []
        # T.flèches = []
        # T.X est une liste de caractère: caractères de la sequence1 precedes  par ''
        sequence1 = self.seq1.toPlainText()
        T.X = ['']
        for caractère in sequence1:
            T.X.append(caractère)
        # T.Y est une liste de caractère: caractères de la sequence2 precedes  par ''
        sequence2 = self.seq2.toPlainText()
        T.Y = ['']
        for caractère in sequence2:
            T.Y.append(caractère)
        # Mise à jour de l'echelle si on dessine sur l'ecran
        if self.destinationFichier == False:
            self.taille_ecran()
        # Les 'descripteurs' X et Y sont dans les marges: abscisses -1 et ordonnees -1
        # Ajoute le caractère vide '∅' en en-tête de X
        c = Cases(chr(8709), 0, -1, T.couleurs['base'])
        T.cases.append(c)
        # Ajoute le caractère vide '∅' en en-tête de Y
        c = Cases(chr(8709), -1, 0, T.couleurs['base'])
        T.cases.append(c)
        for i in range(1, len(T.X)):
            c = Cases(T.X[i], i, -1, T.couleurs['base'])
            T.cases.append(c)
        for j in range(1, len(T.Y)):
            c = Cases(T.Y[j], -1, j, T.couleurs['base'])
            T.cases.append(c)

    def initialise_image_vierge(self, largeur, hauteur):
        """ Créé une première image dans self.images qui est une image vierge
        Pixels blancs, trasparence totale.
        """
        image = QImage(largeur, hauteur, QImage.Format_ARGB32)
        for y in range(hauteur):
            for x in range(largeur):
                image.setPixel(x, y, 0x00FFFFFF)  # Impose un pixel transparent
        # Initialise la liste des images avec l'image vierge
        self.images = [image]

    def mise_a_jour_chemin(self):
        """ Relance la mise à jour de l'affichage des chemins à la suite d'une
        modification du QSpinBox associe
        """
        T = self.dessin.reso
        maxParamSolution = max(0, len(T.chemins)-1)
        self.spinSelectionPlsc.setMaximum(maxParamSolution+1)
        if self.spinSelectionPlsc.value() >= maxParamSolution+1:
            self.spinSelectionPlsc.setValue(0)
        self.spinSelectionPlsc.setMinimum(-1)
        if self.spinSelectionPlsc.value() <= -1:
            self.spinSelectionPlsc.setValue(maxParamSolution)
        chemin_selection = self.spinSelectionPlsc.value()
        if self.boxSelectionUnePlsc.isChecked() or self.boxSelectionToutesPlsc.isChecked():
            self.efface_traces()
            piste = T.chemins[chemin_selection]
            self.dessine_trace(piste)
        self.dessine_nouvelle_image()
        self.dessin.repaint()

    def recherche_plsc(self):
        """ Initialise le tableau de recherche et le dessin du tableau
        Construit le tableau dans le sens de lecture (gauche/droite, haut/bas)
        Selon les cases cochée dans le paramétrage, dessine et/ou  mémorise les
        dessins des étapes.
        Lance le retour sur trace (backtracking) et le dessin/mémorisation des étapes.
        """
        # Si la complétion du tableau vient d'être cochée mais que l'initialisation n'est pas encore cochée
        if self.boxCompletion.isChecked():
            if self.boxInitialisation.isChecked() == False:
                self.boxInitialisation.setCheckState(
                    True)  # Force l'initialisation
                self.boxInitialisation.setCheckState(True)
                return
                # Sort de la recherche car la modification de l'état de boxInitialisation va le relancer
        else:  # Si la complétion est décochée alors les parcours de Plsc ne peuvent pas être affichés
            self.boxSelectionUnePlsc.setCheckState(False)
            self.boxSelectionToutesPlsc.setCheckState(False)
        self.initialisation()
        # Lance la mise à jour des elements à dessiner (Cases et flèches)
        T = self.dessin.reso
        duree = self.temps_par_image()
        # Parcours toutes les colonne de  chaque ligne pour creer les cases
        # et mettre à jour les flèches et les ponts
        for ligne in range(1, len(T.Y)):
            for colonne in range(1, len(T.X)):
                if T.X[colonne] == T.Y[ligne]:
                    couleur_ref = 'actif'
                    T.tableau[ligne][colonne] = T.tableau[ligne-1][colonne-1]+1
                    valeur = T.tableau[ligne][colonne]
                    T.ponts[valeur].append((colonne, ligne))
                    c = Cases(str(valeur), colonne, ligne,
                              T.couleurs['neutre'], False)
                    T.cases.append(c)
                    type_flèche = 'vert_actif'
                else:
                    couleur_ref = 'alerte'
                    haut = T.tableau[ligne-1][colonne]
                    gauche = T.tableau[ligne][colonne-1]
                    T.tableau[ligne][colonne] = max(haut, gauche)
                    c = Cases(str(T.tableau[ligne][colonne]),
                              colonne, ligne, T.couleurs['neutre'], False)
                    T.cases.append(c)
                    type_flèche = 'rouge_max'
                if self.boxCompletion.isChecked():
                    c.visible = True
                    T.flèches[ligne][colonne] = type_flèche
                    case_active_X = T.cherche_case(-1, ligne)
                    case_active_Y = T.cherche_case(colonne, -1)
                    case_active_X.couleur = T.couleurs[couleur_ref]
                    case_active_Y.couleur = T.couleurs[couleur_ref]
                    sleep(duree)
                    self.dessine_nouvelle_image()
                    self.dessin.repaint()
                    case_active_X.couleur = T.couleurs['base']
                    case_active_Y.couleur = T.couleurs['base']
        if self.boxCompletion.isChecked():
            self.dessin.repaint()
        if self.boxSelectionUnePlsc.isChecked() or self.boxSelectionToutesPlsc.isChecked():
            j_max = len(T.tableau)-1  # Indice max des lignes
            i_max = len(T.tableau[0])-1  # Indice max des colonnes
            valeur_max = T.tableau[j_max][i_max]  # Valeur de la dernière case
            T.chemins = T.backtracking_mem(i_max, j_max, valeur_max, [])
        else:
            T.chemins = []
        maxParamSolution = max(0, len(T.chemins)-1)
        self.spinSelectionPlsc.setMaximum(maxParamSolution)
        chemin_selection = self.spinSelectionPlsc.value()
        PLSC_solution = T.chemin_vers_chaîne(chemin_selection)
        self.reponse.setPlainText(PLSC_solution)
        if self.boxSelectionUnePlsc or self.boxSelectionToutesPlsc:
            self.mise_a_jour_chemin()

    def redimensionne_flèches(self):
        D = self.dessin
        ech = D.echelleDessin
        ech_int = int(ech*2//3)
        D.flèche_verte.load("tab_fleche_verte.png")
        D.flèche_vertgris.load("tab_fleche_vertgris.png")
        D.flèche_rouge.load("tab_fleche_rouge.png")
        D.flèche_verte_mini = D.flèche_verte.scaled(ech_int, ech_int)
        D.flèche_vertgris_mini = D.flèche_vertgris.scaled(ech_int, ech_int)
        D.flèche_rouge_mini = D.flèche_rouge.scaled(ech_int, ech_int)

    def selection_Plsc_Une(self):
        """ Declenche par le changement d'etat de la boxSelectionUnePlsc
        Calcul les PLSC et relance le dessin
        """
        # Si la sélection d'Une Plsc vient d'être cochée alors on force la complétion du tableau
        if self.boxSelectionUnePlsc.isChecked() and self.boxCompletion.isChecked() == False:
            self.boxCompletion.setCheckState(True)
            return
        # La case est cochée et que la case 'Toutes' était cochée
        if self.boxSelectionUnePlsc.isChecked() and self.boxSelectionToutesPlsc.isChecked():
            self.boxSelectionToutesPlsc.setCheckState(False)
            self.spinSelectionPlsc.setEnabled(False)
            return
        self.recherche_plsc()

    def selection_Plsc_Toutes(self):
        """ Declenche par le changement d'etat de la boxSelectionToutesPlsc
        Calcul les PLSC et relance le dessin
        """
        # Si la sélection de Toutes les Plsc vient d'être cochée alors on force la complétion du tableau
        if self.boxSelectionToutesPlsc.isChecked() and self.boxCompletion.isChecked() == False:
            self.boxCompletion.setCheckState(True)
            return
        # La case est cochée et que la case 'Une' était cochée
        if self.boxSelectionUnePlsc.isChecked() and self.boxSelectionToutesPlsc.isChecked():
            self.boxSelectionUnePlsc.setCheckState(False)
            self.spinSelectionPlsc.setEnabled(True)
            return
        self.spinSelectionPlsc.setEnabled(
            self.boxSelectionToutesPlsc.isChecked())
        self.recherche_plsc()

    def taille_ecran(self) -> tuple:
        """ Renvoie un n-uplet constitue de :
        largeur de la fenêtre, hauteur de la fenêtre, largeur dessin , hauteur dessin
        Recalcule la valeur de self.dessin.echelleDessin
        genère les images miniatures des flèches
        """
        D = self.dessin
        dimensions_ecran = QDesktopWidget().screenGeometry()
        largeur_ecran = dimensions_ecran.width()
        hauteur_ecran = dimensions_ecran.height()
        # Recupère les paramètres de la zone de dessin
        # largeur utile de la zone de dessin
        largeurDessin = D.size().width()
        # hauteur utile de la zone de dessin
        hauteurDessin = D.size().height()
        largeur, hauteur = self.calculEchelle(largeurDessin, hauteurDessin)
        # Redimensionnement des flèches à partir des flèches d'origines
        self.redimensionne_flèches()
        return (largeur_ecran, hauteur_ecran, largeurDessin, hauteurDessin)

    def temps_par_image(self):
        """ Renvoie le temps en ms de chaque image de l'animation
        """
        T = self.dessin.reso
        duree_totale = self.spinCompletion.value()
        nb_cases = max(1, (len(T.X)) * (len(T.Y)))
        duree = duree_totale / nb_cases
        return duree


def conversion_QImages_vers_GIF(listeQImages: list) -> list:
    """Prend une liste de QImages et la converti en liste d'Images (PIL)
    en prevision d'une exportation en GIF anime
    Renvoie la liste de GIF
    """
    # Initialisation
    listeImagesGIF = []
    # Parcours de la liste des QImages
    for numeroImage in range(len(listeQImages)):
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        imageQt = listeQImages[numeroImage]
        # Conversion au format PNG
        # imageQt.save('tempo/_Qtemp' + str(numeroImage) + '.png')
        imageQt.save(buffer, "png")
        imagePil = Image.open(io.BytesIO(buffer.data()))
        # Ajout de cette image à la liste de sortie
        listeImagesGIF.append(imagePil)
        # imagePil.save('tempo/_temp' + str(numeroImage) + '.png')
    return listeImagesGIF
