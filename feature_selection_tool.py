# -*- coding: utf-8 -*-
"""Modulo per la selezione di una feature.

Descrizione
-----------

Librerie/Moduli
-----------------
    
Note
-----


Autore
-------

- Creato da Sandro Moretti il 09/02/2022.
  Dedagroup spa.

Membri
-------
"""
from qgis.gui import QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import pyqtSignal

# 
#-----------------------------------------------------------
class FeatureSelectionTool(QgsMapToolIdentifyFeature):

    # signal
    featuresIdentified = pyqtSignal(object, list)


    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolIdentifyFeature.__init__(self, self.canvas)
        
    def keyPressEvent( self, e ):
        pass # disable escape key event to prevent loosing maptool
        
    def canvasReleaseEvent(self, mouseEvent):
        results = self.identify(
            mouseEvent.x(), mouseEvent.y(), self.TopDownStopAtFirst, [], self.VectorLayer)
        if len(results) > 0:
            res = results[0]
            features = []
            layer = res.mLayer
            for res in results:
                if res.mLayer == layer:
                    features.append(res.mFeature.id())

            self.featuresIdentified.emit(layer, features)
