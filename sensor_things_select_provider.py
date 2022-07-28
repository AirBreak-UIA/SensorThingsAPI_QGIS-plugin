# -*- coding: utf-8 -*-
"""SensorThings API source select provider

Description
-----------

Derived class to implement custom sorce select provider.

Libraries/Modules
-----------------

- None.
    
Notes
-----

- None.


Author(s)
---------

- Created by Sandro Moretti on 09/02/2022.
 Dedagroup Spa.

Members
-------
"""
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRenderContext, QgsSimpleMarkerSymbolLayer

from SensorThingsAPI.providers.source_select_provider_frost import (
    FrostDataSourceWidget,
    FrostSourceSelectProvider
)

from SensorThingsAPI import plgConfig

# 
#-----------------------------------------------------------
class SensorThingsFrostDataSourceWidget(FrostDataSourceWidget):
    """UI widget class for load a Frost layer"""
    
    def __init__(self, parent, fl=Qt.WindowFlags(), widgetMode=0, options=None):
        """Constructor"""
        super().__init__(parent, fl, widgetMode, options)
        
    def _customizeInternalMessages(self):
        """Customize internal messages"""
        return {
            'Group': self.tr("Group"), 
            'Properties': self.tr("Properties"),
            'Count': self.tr("Count"),
            'HttpError': self.tr("HTTP request failed; response code"),
            'Loading': self.tr("Loading layer"),
            'Loaded': self.tr("Loaded layer"),
            'ConfirmRemove': self.tr("Confirm deletion"),
            'ConnRemove': self.tr('Are you sure you want to remove connection'),
            'Connecting': self.tr('Connecting endpoint'),
            'ReadRecords': self.tr("Read endpoint records")
        }
        
    def _applyLayerStyle(self, layer):
        """Apply style to layer"""
        try:
            # get symbol properties
            cfg_styles = plgConfig.get_value('layer/styles', {})
            properties = cfg_styles.get('default', {})
            
            symbol_size = properties.get('pointRadius', 8)
            symbol_color = properties.get('undefColor', 'gray')
            symbol_fill_opacity = properties.get('fillOpacity', 1.0)
            symbol_stroke_width = properties.get('strokeWidth', 1)
            
            # init
            map_settings = iface.mapCanvas().mapSettings()
            context = QgsRenderContext.fromMapSettings(map_settings)
            symbols = layer.renderer().symbols(context)
            if symbols:
                symb = symbols[0]
                color = symb.color()
            else:
                color = QColor(symbol_color)   
            
            # create simple symbol
            symbol_layer = QgsSimpleMarkerSymbolLayer(size=symbol_size)
            # set setStrokeColor color
            symbol_layer.setStrokeColor(color)
            # set fill color
            fill_color = QColor(color)
            fill_color.setAlphaF(symbol_fill_opacity)
            symbol_layer.setFillColor(fill_color)
            # set stroke width
            symbol_layer.setStrokeWidth(symbol_stroke_width)
            
            # replace the default symbol layer with the new symbol layer
            layer.renderer().symbols(context)[0].changeSymbolLayer(0, symbol_layer)

        except:
            pass

# 
#-----------------------------------------------------------
class SensorThingsFrostSourceSelectProvider(FrostSourceSelectProvider):
    """Derived Source Select Provider"""
    
    def __init__(self, options=None):
        super().__init__()
        self._options = options or {}
    
    def createDataSourceWidget(self, parent, fl, widgetMode):
        """Factory method to return a Data Source Widget"""
        return SensorThingsFrostDataSourceWidget(parent, fl, widgetMode, self._options)
    
    