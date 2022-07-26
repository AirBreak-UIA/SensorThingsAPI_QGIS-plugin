# -*- coding: utf-8 -*-
"""Modulo per la visualizzazione delle informazioni di una postazione.

Descrizione
-----------

Librerie/Moduli
-----------------
    
Notes
-----

- None.

Autore
-------

- Creato da Sandro Moretti il 09/02/2022.
  2022 Dedagroup spa.

Membri
-------
"""

# Qgis\PyQt5 modules
from qgis.PyQt.QtCore import pyqtSlot, Qt, QUrl, QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt import QtWidgets
from qgis.core import QgsWkbTypes, QgsProject, QgsMapLayer
from qgis.gui import QgsGui, QgsRubberBand
from qgis.utils import iface

# plugin modules
from SensorThingsAPI import plgConfig, __QGIS_PLUGIN_NAME__ 
from SensorThingsAPI.log.logger import QgisLogger as logger
from SensorThingsAPI.html.generate import htmlUtil
from SensorThingsAPI.sensor_things_osservazioni_dlg import SensorThingsObservationDialog
from SensorThingsAPI.sensor_things_browser import (SensorThingsRequestError, 
                                                   SensorThingsWebView, 
                                                   SensorThingsNetworkAccessManager)


# 
#-----------------------------------------------------------
class SensorThingsLocationDialog(QtWidgets.QDialog):
    """Dialog to show Location info"""
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    def __init__(self, plugin, parent=None, flags=Qt.WindowFlags()):
        """Constructor
        
        :param parent: 
        :type parent: QtWidgets
        """
        # init
        super().__init__(parent, flags)
        QgsGui.enableAutoGeometryRestore(self)
        
        self.plugin = plugin
        self.page_data = {}
        self.replyPromise = None
        self._lay_id = None
        self._feat_id = None
        self._fids = []
        self._rubberBand = None
        
        # setting the minimum size
        self.setMinimumSize(900, 500)
        
        # add widgets
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        self.webView = SensorThingsWebView(parent=self)
        self.webView.injectPyToJs(self, 'pyjsapi')
        self.layout().addWidget(self.webView)
        
        self.osservazDlg = SensorThingsObservationDialog(self.plugin, parent=self)
        
        # settings
        self.setWindowTitle(self.tr("Location"))
        
    # --------------------------------------
    # 
    # --------------------------------------
    def closeEvent(self, _):
        """Close event method"""
        # reset
        self.page_data = {}
        logger.restoreOverrideCursor()
        # close Observations dialog
        self.osservazDlg.close()
        # remove rubber band
        self._removeRubberBand()
    
    
    # --------------------------------------
    # 
    # --------------------------------------
    def show(self, layer, fid, fids):
        """Show a location info"""
        try:
            # init
            self._lay_id = layer.id()
            self._feat_id = fid
            self._fids = fids or []
            
            # remove rubber band
            self._removeRubberBand()
            
            # get feature
            feature = layer.getFeature(self._feat_id)
            if not feature:
                return
            
            # show rubber band
            self._showRubberBand(layer, feature)
            
            # collect features info
            feats_info = []
            for fid in fids:
                feat = layer.getFeature(fid)
                if feat:
                    feats_info.append({
                        'fid': fid,
                        'locId': feat.attribute( "id" ),
                        'locName': feat.attribute( "name" ),
                        'lodDesc': feat.attribute( "description" )
                    })
                    
            # hide Osservazioni dialog
            self.osservazDlg.hide()
            
            # show wait cursor
            logger.setOverrideCursor()
            
            # get faeature location attribute
            location_id = feature.attribute( "id" )
            location_name = feature.attribute( "name" )
            location_desc = feature.attribute( "description" )
            
            # compose url
            provider = layer.dataProvider()
            service_url = QUrl(provider.dataSourceUri())
            if not service_url.isValid():
                raise ValueError(
                    "{}: {}".format(self.tr("Invalid layer URL"), service_url.toString()))
                
            # prepare data for HTM template
            self.page_data = {
                'locale': self.plugin.locale,
                'base_folder': htmlUtil.getBaseUrl(),
                'feature': {
                    'fid': self._feat_id,
                    'locId': location_id,
                    'locName': location_name,
                    'lodDesc': location_desc
                },
                'features': feats_info,
                'location': None,
                'things': None,
            }    
                
            # Request location data asyncronously
            url = service_url.resolved(QUrl(f"./Locations({location_id})")).toString()
            request = self.getRequest()
            request.resolved.connect(self._location_callback)
            request.get(url, { "tag": 'Location' })
            
            # show spinner
            self._show_web_spinner(True)
            
        except SensorThingsRequestError as ex:
            logger.restoreOverrideCursor()
            self.logError(
                "{}: {}".format(self.tr("Location dialog visualization"), str(ex)))
            
        except Exception as ex:
            logger.restoreOverrideCursor()
            self.logError(
                "{}: {}".format(self.tr("Location dialog visualization"), str(ex)))
    
    # --------------------------------------
    # 
    # --------------------------------------
    def logError(self, message):
        """Log error message"""
        # hide spinner
        self._show_web_spinner(False)
        # log
        logger.msgbar(
            logger.Level.Critical, 
            str(message), 
            title=__QGIS_PLUGIN_NAME__,
            clear=True
        ) 
        logger.msgbox(
            logger.Level.Critical, 
            str(message),  
            title=__QGIS_PLUGIN_NAME__
        )
        
    # --------------------------------------
    # 
    # --------------------------------------
    def rejectRequest(self, message):
        """Show Observations dialog"""
        # hide spinner
        self._show_web_spinner(False)
        # restore cursor
        logger.restoreOverrideCursor()
        if message:
            self.logError(str(message))
        
    
    # --------------------------------------
    # 
    # --------------------------------------
    def _show_web_spinner(self, show):
        frame =self.webView.page().mainFrame()
        if show:
            frame.evaluateJavaScript("sensorThingsShowSpinner(true);")
        else:
            frame.evaluateJavaScript("sensorThingsShowSpinner(false);")
        
    # --------------------------------------
    # 
    # --------------------------------------    
    def _show_callback(self):
        try:
            # check if got all data 
            if self.page_data.get('location') is None or\
               self.page_data.get('things') is None:
                self.rejectRequest(None)
                return
            
            logger.restoreOverrideCursor()
           
            # load HTL document 
            template_name = 'location.html'
            template = htmlUtil.generateTemplate(template_name)
            self.webView.setHtml(template.render(self.page_data))
        
            # show dialog 
            QtWidgets.QDialog.show(self)
           
        except Exception as ex:
            self.logError(
                "{}: {}".format(self.tr("Location dialog visualization"), str(ex)))
    
    # --------------------------------------
    # 
    # --------------------------------------
    def _location_callback(self, loc_data):
        try:
            if not self.page_data:
                self.rejectRequest(None)
                return
            
            # store data
            self.page_data['location'] = loc_data or {}
            
            # Request things data asyncronously
            url = loc_data.get('Things@iot.navigationLink', None)
            if url is None:
                raise ValueError(self.tr('Things URL not valued'))
            request = self.getRequest()
            request.resolved.connect(self._things_callback)
            request.get(url, { "dataSrc": "value", "tag": 'Things' })
           
        except Exception as ex:
            self.logError(
                "{}: {}".format(self.tr("Location dialog visualization"), str(ex)))
    
    
    # --------------------------------------
    # 
    # --------------------------------------        
    def _things_callback(self, things_data):
        try:
            if not self.page_data:
                self.rejectRequest(None)
                return
            
            # store data
            self.page_data['things'] = things_data or []
            # try to show dialog
            self._show_callback()
           
        except Exception as ex:
            self.logError(
                "{}: {}".format(self.tr("Location dialog visualization"), str(ex)))
        
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    def _showRubberBand(self, layer, feature):
        """Show rubber band in scene"""
        # remove previous rubber band
        self._removeRubberBand()
        
        try:
            # create rubber band
            canvas = iface.mapCanvas()
            geom = feature.geometry()
            geomType = geom.type()
            
            color = QColor("red")
            color.setAlphaF(0.78)
            fillColor = QColor(255, 71, 25, 150)
        
            self._rubberBand = QgsRubberBand(canvas, geomType)
            self._rubberBand.setColor(color)
            self._rubberBand.setFillColor(fillColor)
              
            if geomType == QgsWkbTypes.PointGeometry:
                cfg_styles = plgConfig.get_value('layer/styles', {})
                properties = cfg_styles.get('default', {})
                symbol_size = properties.get('pointRadius', 8)
                
                self._rubberBand.setWidth(symbol_size * 5)
                self._rubberBand.setIcon(QgsRubberBand.ICON_CIRCLE)
                self._rubberBand.addPoint(geom.asPoint(), True, 0, 0)
            else:
                self._rubberBand.addGeometry(geom, layer)
                self._rubberBand.setWidth(5)
                
            
            # show rubber band    
            self._rubberBand.show()
        except:
            pass
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    def _removeRubberBand(self):
        """Remove rubber band from scene"""
        if self._rubberBand:
            canvas = iface.mapCanvas()
            canvas.scene().removeItem(self._rubberBand)
            self._rubberBand = None
    
    
    @pyqtSlot(result=QVariant)
    def getPageData(self):
        """Injected method to get page data"""
        return self.page_data
    
    @pyqtSlot(str, result=QVariant)
    def getThingData(self, thing_id):
        """Injected method to get thing data"""
        try:        
            # Get thing data
            things_data = self.page_data.get('things', {})
            thing_data = next((i for i in things_data if str(i['@iot.id']) == str(thing_id)), None)
            if not thing_data:
                raise ValueError(self.tr("Invalid Thing ID"))
            return thing_data
        
        except Exception as ex:
            self.logError(str(ex))
            return {}
        
    @pyqtSlot(str, QVariant, result=QVariant)
    def loadData(self, url, options):
        """Injected method to get data synchronously"""
        try:      
            options = options if isinstance(options, dict) else {}
            tag = options.get("tag", "")
              
            # Request datastream data
            return SensorThingsNetworkAccessManager.requestExternalData(url, options) or {}
        
        except Exception as ex:
            self.logError(
                "{} {}: {}".format(self.tr("Loading data"), tag, str(ex)))
    
    @pyqtSlot(result=QVariant)
    def getRequest(self):
        """Injected method to return a new request to get data asynchronously"""
        try:
            # Create request async
            self.replyPromise = SensorThingsNetworkAccessManager.requestExternalDataAsync(parent=self)
            self.replyPromise.rejected.connect(self.rejectRequest)
            return self.replyPromise 
            
        except Exception as ex:
            self.logError(str(ex))
            return None
            
            
    @pyqtSlot(QVariant, QVariant)
    def loadObservationsData(self, ds_row, options):
        """Show a new Osservazioni dialog"""
        try:
            # check if visible 
            if not self.isVisible():
                return
            
            # init
            self.osservazDlg.hide()
            ds_row = ds_row or {}
            options = options or {}
            date_filter = options.get('filterTime', '')
            query_params = options.get('queryParams', '')
            is_multidatastream = bool(options.get('isMultidatastream', False))
                    
            # Request Osservazioni data
            self.page_data['selectRow'] = ds_row
            self.page_data['filterTime'] = date_filter
            self.page_data['queryParams'] = query_params
            self.page_data['isMultidataStream'] = is_multidatastream
            
            # create a new Osservazioni dialog
            self.osservazDlg.show(self.page_data)
            
            
        except Exception as ex:
            self.logError(
                "{}: {}".format(self.tr("Loading Observations data"), str(ex)))
            
            
    @pyqtSlot(str)
    def changeLocation(self, str_fid):
        """Injected method to location in multi feature selection"""
        
        # init
        if self._lay_id is None or\
           self._feat_id is None:
            return
        
        fid = int(str_fid)
        
        # search layers in TOC
        root_node = QgsProject.instance().layerTreeRoot()
        tree_layer = root_node.findLayer(self._lay_id)
        if tree_layer:
            layer = tree_layer.layer()
            # check if vector layer
            if layer.type() == QgsMapLayer.VectorLayer:
                # show Location info
                self.show(layer, fid, self._fids)
       
            