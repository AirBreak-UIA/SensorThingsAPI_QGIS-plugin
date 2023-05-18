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
import os
import csv

# Qgis\PyQt5 modules
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt import QtWidgets

# plugin modules
from SensorThingsAPI import __QGIS_PLUGIN_NAME__, plgConfig
from SensorThingsAPI.log.logger import QgisLogger as logger
from SensorThingsAPI.util.file import FileUtil
from SensorThingsAPI.html.generate import htmlUtil 
from SensorThingsAPI.sensor_things_browser import (SensorThingsWebView, 
                                                   SensorThingsRequestError, 
                                                   SensorThingsNetworkAccessManager)



# 
#-----------------------------------------------------------
class SensorThingsObservationDialog(QtWidgets.QDialog):
    """Dialog to show Observations info"""
    
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
        
        self.plugin = plugin
        self.page_data = {}
        self.csv_options = {}
        self.replyPromise = None
        
        # add widgets
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        self.webView = SensorThingsWebView(parent=self)
        self.webView.injectPyToJs(self, 'pyjsapi')
        self.layout().addWidget(self.webView)
        
        # settings
        self.setWindowTitle(self.tr("Observations"))
    
    # --------------------------------------
    # 
    # --------------------------------------
    def logError(self, message, level=logger.Level.Critical):
        """Log error message"""
        logger.msgbar(
            level, 
            str(message), 
            title=__QGIS_PLUGIN_NAME__,
            clear=True
        )
        
        logger.msgbox(
            level, 
            str(message),  
            title=__QGIS_PLUGIN_NAME__
        )
        
    # --------------------------------------
    # 
    # --------------------------------------
    def rejectRequest(self, message):
        """Show Observations dialog"""    
        message = str(message)
        self.logError(message)
        # hide spinner
        self._show_web_spinner(False)
        
    # --------------------------------------
    # 
    # --------------------------------------
    def show(self, data):
        """Show Osservazioni grid"""
        try:
            # init 
            self.page_data = data or {}
            self.csv_options = {}
            
            # add config
            self.page_data['chart_opts'] = plgConfig.get_value('chart',{})
            
            # load HTL document 
            template_name = 'observations.html'
            template = htmlUtil.generateTemplate(template_name)
            self.webView.setHtml(template.render(self.page_data)) 
            
            # show dialog 
            QtWidgets.QDialog.show(self)
            
        except SensorThingsRequestError as ex:
            logger.msgbar(
                logger.Level.Critical,
                "{}: {}".format(self.tr("Observations dialog visualization"), str(ex)), 
                title=__QGIS_PLUGIN_NAME__)
            
        except Exception as ex:
            logger.msgbar(
                logger.Level.Critical, 
                "{}: {}".format(self.tr("Observations dialog visualization"), str(ex)),
                title=__QGIS_PLUGIN_NAME__)
    
    
    def _show_web_spinner(self, show):
        frame =self.webView.page().mainFrame()
        if show:
            frame.evaluateJavaScript("sensorThingsShowSpinner(true);")
        else:
            frame.evaluateJavaScript("sensorThingsShowSpinner(false);")
    
    def _export_csv_callback(self, oss_data):
        """Private method to export observations to CSV file"""
        try:
            # check if visible 
            if not self.isVisible():
                return
            if not self.csv_options:
                return
            
            # hide spinner
            self._show_web_spinner(False)
            
            # init
            options = self.csv_options or {}
            export_fields = options.get('exportFields', {})
            open_file_flag = options.get('openFile', False)
            date_range_text = options.get('dateRange', '')
            file_name = options.get('fileName', '')
            file_name_proposed = file_name
            
            # check if valid result data
            if not isinstance(oss_data, list):
                raise ValueError(self.tr("Returned malformed data"))
            
            # check if there are records
            if not oss_data:
                logger.msgbox(
                    logger.Level.Warning, 
                    "{}: \n{}".format(self.tr("No observations found in the range of dates"), date_range_text),
                    title=__QGIS_PLUGIN_NAME__
                )
                return
            
            # config export
            cfg_export = plgConfig.get_value('export',{})
            fld_delimiter = str(cfg_export.get('field_delimiter_char', '')).strip()
            fld_delimiter = fld_delimiter[:1] or ','
            
            # loop while file permission denied 
            while True:
                # ask where to save file    
                file_path, _ = QFileDialog.getSaveFileName(
                    self, self.tr('Save the Observations file'), file_name_proposed, 'CSV(*.csv)')
                if not file_path:
                    return
                    
                try:
                    # create CSV file
                    with open(str(file_path), 'w', newline='\n', encoding='utf-8') as stream:
                        writer = csv.writer( stream, delimiter=fld_delimiter, lineterminator='\n' )
                        # write header
                        writer.writerow(export_fields.keys())
                        # write records
                        for row in oss_data:
                            row_data = []
                            
                            # get values
                            for _, fld in export_fields.items():
                                field_name = fld.get('field', '')
                                field_value = row.get(field_name, '')
                                try:
                                    if 'index' in fld:
                                        field_index = int(fld.get('index'))
                                        field_value = field_value[field_index]      
                                except (TypeError, IndexError):
                                    field_value = ''
                                
                                # collect value
                                row_data.append(field_value)
                                
                            # write record
                            writer.writerow(row_data)
                    
                    # open downloaded file
                    if open_file_flag:
                        os.startfile(os.path.normpath(file_path))
                    
                    # exit loop        
                    return
                
                except PermissionError as ex:
                    # correct name with a postfix
                    file_name_proposed, _ = FileUtil.getPrefixFileName(file_name)
                    # show alert message
                    self.logError(
                        "{}: \n{}".format(self.tr("File access denied"), file_path),
                        level=logger.Level.Warning)
                    
        except Exception as ex:
            self.logError(str(ex))
            return
    
    
    @pyqtSlot(result=QVariant)
    def getPageData(self):
        """Injected method to get page data"""
        return self.page_data
    
    
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
        
    @pyqtSlot(str, QVariant)
    def exportCSV(self, url, options):
        """Injected method to request export observations to CSV file"""
        try:
            # show spinner
            self._show_web_spinner(True)
            
            # init
            self.csv_options = options or {}
            # request data asyncronously
            request = self.getRequest()
            request.resolved.connect(self._export_csv_callback)
            request.get(url, options)
            
            
        except Exception as ex:
            self.logError(str(ex))
            return False
    