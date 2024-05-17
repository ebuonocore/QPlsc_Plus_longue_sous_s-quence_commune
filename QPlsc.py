# coding: utf-8
"""
Programme principal de la recherche d'une (PLSC) plus longue sous-séquence
commune entre deux chaînes
Eric Buonocore. Le 21/06/2021

Vérifier les exportations
Si rien n 'est coché, on ne dessine que les axes
Parcours cyclique des PLSC
Ne pas afficher PLSC si rien n'est coché
Export Image => que la dernière image
"""

from qtpy.QtWidgets import (QApplication, QFrame)
from QPlscFenetres import *
from QPlscStructures import *

# ********** Corps du programme **********
# Lance l'application
app=QApplication(sys.argv)
# Création de la fenêtre princiale de type Fenetre
frame = Fenetre()
# Affichhe le composant principale de frame
frame.widgetP.show()
sys.exit(app.exec_())
