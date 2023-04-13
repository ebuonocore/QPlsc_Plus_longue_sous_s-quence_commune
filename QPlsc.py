"""
Programme principal de la recherche d'une (PLSC) plus longue sous-séquence
commune entre deux chaînes
Eric Buonocore. Le 21/06/2021

Zones noires au niveau des transparences des flèches ?!?
Tristate des bcheckbox reste actif: Grise = True ?!
Supprimer calculEchelle et initialise_image_vierge de self.capture()
"""

from qtpy.QtWidgets import (QApplication, QFrame)
from QPlscFenetres import *
from QPlscStructures import *

# ********** Corps du programme **********
# Lance l'application
app = QApplication(sys.argv)
# Création de la fenêtre princiale de type Fenetre
frame = Fenetre()
# Affichhe le composant principale de frame
frame.widgetP.show()
sys.exit(app.exec_())
